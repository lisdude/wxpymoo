import wx
import wx.lib.newevent
import utility

PrefsChangedEvent, EVT_PREFS_CHANGED = wx.lib.newevent.NewEvent()

_config      = None
_defaults   = {
    'fgcolour' : '#839496',
    'bgcolour' : '#002b36',
    'font'     :  wx.Font( 12, wx.TELETYPE, wx.NORMAL, wx.NORMAL ).GetNativeFontInfoDesc(),

    'save_window_size' : True,
    'window_width'     : 800,
    'window_height'    : 600,
    'input_height'     : 25,

    # 'theme'        : 'solarized',

    'use_ansi'             : True,
    'use_mcp'              : True,
    'highlight_urls'       : True,
    'save_mcp_window_size' : True,
    # TODO -- make this default to False, but currently having no connection
    # at start-time breaks mainwindow
    'autoconnect_last_world'  : True,

    'mcp_window_width'  : 600,
    'mcp_window_height' : 400,

    'external_editor'  : 'gvim -f',
    'use_x_copy_paste' : utility.platform == 'linux',
}

def Initialize():
    global _config

    _config = wx.FileConfig()

    for default in _defaults.items():
        (key, def_val) = default
        # if nothing exists for that key, set it to the default.
        if not get(key):
            set(key, str(def_val))

def get(val): return _config.Read(val)
def set(param, val):
    global _config

    _config.Write(param, str(val))
    _config.Flush()

def update(pw):
    # pw == prefs_window
    # This is doing some nasty GetAsString and GetNativeFontInfoDesc foo here,
    # instead of encapsulated in prefs, which I think I'm OK with.

    set('save_window_size',       pw.general_page.save_size_checkbox.GetValue() )
    set('autoconnect_last_world', pw.general_page.autoconnect_checkbox.GetValue() )

    set('font',     pw.fonts_page.font_ctrl.GetSelectedFont().GetNativeFontInfoDesc())
    set('fgcolour', pw.fonts_page.fgcolour_ctrl.GetColour().GetAsString(wx.C2S_HTML_SYNTAX))
    set('bgcolour', pw.fonts_page.bgcolour_ctrl.GetColour().GetAsString(wx.C2S_HTML_SYNTAX))
    set('use_ansi', pw.fonts_page.ansi_checkbox.GetValue() )

    set('external_editor', pw.paths_page.external_editor.GetValue() )

    wx.PostEvent(pw.parent, PrefsChangedEvent())

