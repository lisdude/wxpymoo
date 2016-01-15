import wx
import wx.richtext

import wxpymoo.prefs as prefs
import wxpymoo.utility

import webbrowser

import re

# TODO we need a better output_filter scheme, probably?
#use WxMOO.MCP21
#use WxMOO.Theme

class OutputPane(wx.richtext.RichTextCtrl):

    def __init__(self, connection):
        self.parent = connection.splitter
        wx.richtext.RichTextCtrl.__init__(self, self.parent,
            style = wx.TE_AUTO_URL | wx.TE_READONLY | wx.TE_NOHIDESEL
        )
        self.input_pane = connection.input_pane

        self.restyle_thyself()

        self.Bind(wx.EVT_SET_FOCUS, self.focus_input)
        self.Bind(wx.EVT_TEXT_URL,  self.process_url_click)
        # TODO - this probably should be a preference, but for now, this is the
        # least-bad default behavior.
        self.Bind(wx.EVT_SIZE,      self.scroll_to_bottom)

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
        basic_style = wx.richtext.RichTextAttr()
        basic_style.SetTextColour      (prefs.get('output_fgcolour'))
        basic_style.SetBackgroundColour(prefs.get('output_bgcolour'))

        self.SetBackgroundColour(prefs.get('output_bgcolour'))
        self.SetBasicStyle(basic_style)

        # is there a way to construct a font directly from an InfoString, instead of making
        # a generic one and then overriding it like this?
        font = wx.NullFont
        font.SetNativeFontInfoFromString(prefs.get('output_font'))
        self.SetFont(font)

    def display(self, text):
        range = self.GetSelectionRange()

        # TODO - ANSI parsing woo
        for line in text.split('\n'):
            line = line + "\n"
            #if (prefs.get('use_mcp')):
                #next unless (line = WxMOO.MCP21.output_filter(line))
            if (True or prefs.get('use_ansi')):
                stuff = self.ansi_parse(line)
                for bit in stuff:
                    #if (bit):
                        #self.apply_ansi(bit)
                    #else:
                        # TODO - this might should be separate from use_ansi.
                        # TODO - snip URLs first then ansi-parse pre and post?
                        if prefs.get('highlight_urls'):
                            matches = re.split(wxpymoo.utility.URL_REGEX, bit)
                            for chunk in matches:
                                if chunk is None: continue
                                if re.match(wxpymoo.utility.URL_REGEX, chunk):
                                    self.BeginURL(chunk)
                                    self.BeginUnderline()
                                    #self.BeginTextColour( self.lookup_color('blue', True) )
                                    self.BeginTextColour( wx.BLUE )

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

#        if (from != to) {
#            self.SetSelection(from, to)
#        }

    def focus_input(self,evt): self.input_pane.SetFocus()

    #theme = wxpymoo.theme.Theme()

    def lookup_color(self, color, bright):
        #return theme.Colour(color, True if self.bright else False)
        pass

    def apply_ansi(self, bit):
        (type, payload) = bit
#        if (type == 'control'):
#            given (payload) {
#                when ('normal')       {
#                    my plain_style = Wx.TextAttr.new
#                    if (self.{'inverse'}) {
#                        say STDERR "I'm inverse!"
#                        self.invert_colors
#                    }
#                    self.SetDefaultStyle(plain_style)
#                }
#                when ('bold')         { self.BeginBold;     }
#                when ('dim')          { self.EndBold;       } # TODO - dim further than normal?
#                when ('underline')    { self.BeginUnderline }
#                when ('blink')     {
#                    # TODO - create timer
#                    # apply style name
#                    # periodically switch foreground color to background
#                }
#                when ('inverse')      { self.invert_colors; }
#                when ('hidden')       { 1; }
#                when ('strikethru')   { 1; }
#                when ('no_bold')      { self.EndBold; }
#                when ('no_underline') { self.EndUnderline }
#                when ('no_blink')  {
#                    # TODO - remove blink-code-handles style
#                }
#                when ('no_strikethru') { 1; }
#            }
#        } elsif (type eq 'foreground') {
#            self.BeginTextColour(self.lookup_color(payload))
#        } elsif (type eq "background") {
#            my bg_attr = Wx.TextAttr.new
#            bg_attr.SetBackgroundColour(self.lookup_color(payload))
#            self.SetDefaultStyle(bg_attr)
#            # self.BeginBackgroundColour(self.lookup_color(payload))
#        } else {
#            say STDERR "unknown ANSI type type"
#        }

    def invert_colors(self):
        current = self.GetStyle(self.GetInsertionPoint())
        fg = current.GetTextColour()
        bg = current.GetBackgroundColour()
        # TODO - hrmn current bg color seems to be coming out wrong.

        current.SetTextColour(bg)
        current.SetBackgroundColour(fg)

        self.inverse = False if self.inverse else True
        # self.SetDefaultStyle(current);  # commenting this out until bg color confusion is resolved

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

    def ansi_parse(self, line):
        #if (my beepcount = line =~ s/\007//g) {
        #    for (1..beepcount) {
        #        say STDERR "found a beep"
        #        Wx.Bell();  # TODO -- "if beep is enabled in the prefs"
        #    }
        #}

        bits = re.split('\e\[(\d+(?:;\d+)*)m', line)

        #my @styled_text
        #while (my (i, val) = each @bits) {
        #    if (i % 2) {
        #        for my c (split /;/, val) {
        #            if (my style = ansi_codes{val}) {
        #                push @styled_text, style
        #            }
        #        }
        #    } else {
        #        push @styled_text, val if val
        #    }
        #}
        #return [@styled_text]
        return [line]

