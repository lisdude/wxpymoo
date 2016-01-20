import wx
import wx.richtext as rtc

import mcp21.core as mcp21
import prefs
import utility
from theme import Theme

import webbrowser

import re

class OutputPane(rtc.RichTextCtrl):

    def __init__(self, parent, connection):
        rtc.RichTextCtrl.__init__(self, parent,
            style = wx.TE_AUTO_URL | wx.TE_READONLY | wx.TE_NOHIDESEL | wx.TE_MULTILINE
        )
        self.input_pane = connection.input_pane

        # state toggles for ANSI processing
        self.bright  = False
        self.inverse = False

        self.theme = Theme()

        # TODO - this probably should be a preference, but for now, this is the
        # least-bad default behavior.
        # TODO 2 -- uncommenting this makes the output_pane be a 1x1 square in the upper left
#        self.Bind(wx.EVT_SIZE                       , self.scroll_to_bottom)
        self.Bind(wx.EVT_SET_FOCUS                   , self.focus_input)
        self.Bind(wx.EVT_TEXT_URL                    , self.process_url_click)
        self.Bind(wx.EVT_MIDDLE_UP                   , self.input_pane.paste_from_selection )
        self.Bind(rtc.EVT_RICHTEXT_SELECTION_CHANGED , self.copy_from_selection )


        self.restyle_thyself()

    def copy_from_selection(self, evt = None):
        print("copying selection")
        uxcp = prefs.get('use_x_copy_paste') == 'True'
        if uxcp and platform == 'linux': wx.TheClipboard.UsePrimarySelection(True)
        self.Copy()
        if uxcp and platform == 'linux': wx.TheClipboard.UsePrimarySelection(False)


    def scroll_to_bottom(self, evt):
        self.ShowPosition(self.GetLastPosition())

    def process_url_click(self, evt):
        url = evt.GetString()
        wx.BeginBusyCursor()
        webbrowser.open(url)
        wx.EndBusyCursor()

    def WriteText(self, rest):
        super(OutputPane, self).WriteText(rest)
        self.ScrollIfAppropriate()

    def is_at_bottom(): True

    def ScrollIfAppropriate(self):
        if (True or self.is_at_bottom() or prefs.get('scroll_on_output')):
            self.scroll_to_bottom(False)

    def restyle_thyself(self):
        basic_style = rtc.RichTextAttr()
        basic_style.SetTextColour      (prefs.get('output_fgcolour'))
        basic_style.SetBackgroundColour(prefs.get('output_bgcolour'))

        self.SetBackgroundColour(prefs.get('output_bgcolour'))
        self.SetBasicStyle(basic_style)
        self.basic_style = basic_style

        # is there a way to construct a font directly from an InfoString, instead of making
        # a generic one and then overriding it like this?
        font = wx.NullFont
        font.SetNativeFontInfoFromString(prefs.get('output_font'))
        self.SetFont(font)

    def display(self, text):
        self.SetInsertionPointEnd()
        for line in text.split('\n'):
            line = line + "\n"
            if (prefs.get('use_mcp')):
                line = mcp21.output_filter(line)
                if not line: continue  # output_filter returns falsie if it handled it.
            if (True or prefs.get('use_ansi')):
                stuff = self.ansi_parse(line)
                for bit in stuff:
                    if type(bit) is list:
                        self.apply_ansi(bit)
                    else:
                        # TODO - this might should be separate from use_ansi.
                        # TODO - snip URLs first then ansi-parse pre and post?
                        if prefs.get('highlight_urls'):
                            matches = re.split(utility.URL_REGEX, bit)
                            for chunk in matches:
                                if chunk is None: continue
                                if re.match(utility.URL_REGEX, chunk):
                                    self.BeginURL(chunk)
                                    self.BeginUnderline()
                                    self.BeginTextColour( self.lookup_colour('blue', True) )

                                    self.WriteText(chunk)

                                    self.EndTextColour()
                                    self.EndUnderline()
                                    self.EndURL()
                                else:
                                    self.WriteText(chunk)
                        else:
                            self.WriteText(bit)
            else:
                self.WriteText(line)

    def focus_input(self,evt): self.input_pane.SetFocus()

    def lookup_colour(self, color, *bright):
        return self.theme.Colour(color,
                True if (bright or self.bright) else False)

    def apply_ansi(self, bit):
        type, payload = bit
        if type == 'control':
            if payload == 'normal':
                self.SetDefaultStyle(self.basic_style)
            elif payload == 'bold':      self.BeginBold()
            elif payload == 'dim':       self.EndBold()    # TODO - dim further than normal?
            elif payload == 'underline': self.BeginUnderline()
            elif payload == 'blink':
                pass
                # TODO - create timer
                # apply style name
                # periodically switch foreground color to background
            elif payload == 'inverse':      self.invert_colors()
            elif payload == 'hidden':       pass
            elif payload == 'strikethru':   pass
            elif payload == 'no_bold':      self.EndBold()
            elif payload == 'no_underline': self.EndUnderline()
            elif payload == 'no_blink':
                pass
                # TODO - remove blink-code-handles style
            elif payload == 'no_strikethru': pass

        elif type == 'foreground':
            self.BeginTextColour(self.lookup_colour(payload))
        elif type == "background":
            bg_attr = rtc.RichTextAttr()
            self.GetStyle(-1, bg_attr) # '-1' == end position
            bg_attr.SetBackgroundColour(self.lookup_colour(payload))
            self.SetDefaultStyle(bg_attr)
        else:
            print("unknown ANSI type:", type)

    def invert_colors(self):
        current = rtc.RichTextAttr()
        self.GetStyle(self.GetInsertionPoint(), current)
        fg = current.GetTextColour()
        bg = current.GetBackgroundColour()
        # TODO - hrmn current bg color seems to be coming out wrong.

        current.SetTextColour(bg)
        current.SetBackgroundColour(fg)

        self.inverse = False if self.inverse else True
        self.SetDefaultStyle(current);  # commenting this out until bg color confusion is resolved

    def ansi_parse(self, line):
        global ansi_codes
        beep_cleaned, count = re.subn("\007", '', line)

        if count:
            line = beep_cleaned
            for b in range(0, count):
                print("found a beep")
                wx.Bell();  # TODO -- "if beep is enabled in the prefs"

        styled_text = []

        bits = re.split('\x1b\[(\d+(?:;\d+)*)m', line)

        if len(bits) > 1:
            # We'll have a list that alternates text, ansicode, text, ansicode....
            for idx, bit in enumerate(bits):
                if bit == '': continue
                # if it's ansi...
                if (idx % 2):
                    # ...split it up and add the style(s) to the styled_text list
                    for code in bit.split(';'):
                        styled_text.append(ansi_codes[int(code)])
                # otherwise it's text, just mash it on there
                else: styled_text.append(bit)
        else:
            styled_text.append(bits[0])

        return styled_text

ansi_codes = {
    0     : [ 'control' , 'normal'        ],
    1     : [ 'control' , 'bold'          ],
    2     : [ 'control' , 'dim'           ],
    4     : [ 'control' , 'underline'     ],
    5     : [ 'control' , 'blink'         ],
    7     : [ 'control' , 'inverse'       ],
    8     : [ 'control' , 'hidden'        ],
    9     : [ 'control' , 'strikethru'    ],
    22    : [ 'control' , 'no_bold'       ], # normal font weight also cancels 'dim'
    24    : [ 'control' , 'no_underline'  ],
    25    : [ 'control' , 'no_blink'      ],
    29    : [ 'control' , 'no_strikethru' ],
    30    : [ 'foreground' , 'black'  ],
    31    : [ 'foreground' , 'red'    ],
    32    : [ 'foreground' , 'green'  ],
    33    : [ 'foreground' , 'yellow' ],
    34    : [ 'foreground' , 'blue'   ],
    35    : [ 'foreground' , 'magenta'],
    36    : [ 'foreground' , 'cyan'   ],
    37    : [ 'foreground' , 'white'  ],

    40    : [ 'background' , 'black'  ],
    41    : [ 'background' , 'red'    ],
    42    : [ 'background' , 'green'  ],
    43    : [ 'background' , 'yellow' ],
    44    : [ 'background' , 'blue'   ],
    45    : [ 'background' , 'magenta'],
    46    : [ 'background' , 'cyan'   ],
    47    : [ 'background' , 'white'  ],
}

