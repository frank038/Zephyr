#!/usr/bin/env python3

VERSION = "0.9.3"
ENAME = "Zephyr"
ESITE = "https://github.com/frank038/Zephyr"

import sys,os
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('GtkSource', '5')
gi.require_version('Pango', '1.0')
gi.require_version("Adw", "1")
from gi.repository import Gtk,Gdk,GLib,Gio,GtkSource,Pango,Adw
import json
import subprocess

self_main = None
_curr_dir = os.getcwd()
_HOME = os.path.expanduser("~")
icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
COMMANDLINE_CWD = None


# the directory settings and options
if not os.access(_curr_dir, os.W_OK):
    HOME_CONFIG = os.path.join(_HOME,".config","ZephyrTE4")
    try:
        if not os.path.exists(HOME_CONFIG):
            os.mkdir(HOME_CONFIG, mode=0o770)
    except:
        HOME_CONFIG = _curr_dir
    if HOME_CONFIG != _curr_dir:
        try:
            shutil.copytree("/usr/share/ZephyrTE/configs", os.path.join(HOME_CONFIG, "configs"))
            shutil.copytree("/usr/share/ZephyrTE/icons", os.path.join(HOME_CONFIG, "icons"))
            shutil.copytree("/usr/share/ZephyrTE/langs", os.path.join(HOME_CONFIG, "langs"))
        except Exception as E:
            HOME_CONFIG = _curr_dir
else:
    HOME_CONFIG = _curr_dir


SCRIPTS_DIRECTORY = os.path.join(HOME_CONFIG, "scripts")
EDITOR_STYLE_CSS = os.path.join(HOME_CONFIG, "configs/windowstyle.css")

sys.path.append(os.path.join(HOME_CONFIG, "langs"))
_lang_names = GLib.get_language_names()
_langs_application = os.listdir(os.path.join(HOME_CONFIG, "langs"))
for l_lang in _lang_names:
    if l_lang+".py" in _langs_application:
        _lang = __import__(l_lang)
        break
else:
    _lang = __import__("en")


config_file = os.path.join(HOME_CONFIG, "configs/config.json")
config_conf_start = { 
"wwidth": 1200, 
"wheight": 800,
"printer-font-size": 10,
"scheme": "cobalt",
"language": "",
"tab-size": 0,
"file-monitoring": 0,
"font-size": 10,
"single-app": 0,
"autoclose-signs": 0,
"hlbackground": "",
"hlforeground": ""
}
if not os.path.exists(config_file):
    try:
        _data_json = config_conf_start
        _ff =  open(config_file, "w")
        json.dump(_data_json, _ff, indent = 4)
        _ff.close()
        config_conf = config_conf_start
    except:
        sys.exit()
else:
    try:
        _ff = open(config_file, "r")
        config_conf = json.load(_ff)
        _ff.close()
    except:
        sys.exit()

######### CONFIGURATION
WWIDTH = config_conf["wwidth"] # this program width
WHEIGHT = config_conf["wheight"] # this program height
PRINTER_FONT_SIZE = config_conf["printer-font-size"] #font size
STYLE_SCHEME = config_conf["scheme"] # 'name'
LANGUAGE_STYLE = config_conf["language"] # 'name' or ''
TAB_SIZE = config_conf["tab-size"] # TAB,2,4,8
FILE_MONITORING = config_conf["file-monitoring"] # 
FONT_SIZE = config_conf["font-size"] # font size
SINGLE_APP = config_conf["single-app"] # one instance of this program
# SIGN_AUTOCLOSE = config_conf["autoclose-signs"]
SIGN_AUTOCLOSE = 0
HLFOREGROUND = config_conf["hlforeground"]
HLBACKGROUND = config_conf["hlbackground"]
#########
TAB_SIZE_LIST = [0,2,4,8]
SIGN_AUTOCLOSE_LIST = ["(","[","{","'",'"',"«","<","?","!"]
SIGN_AUTOCLOSE_LIST_NEXT = [")","]","}","'",'"',"»",">","¿","¡"]


MENU_XML="""
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <menu id="app-menu">
    <section>
      <item>
        <attribute name="action">win.new</attribute>
        <attribute name="label" translatable="yes">{}</attribute>
      </item>
      <item>
        <attribute name="action">win.open</attribute>
        <attribute name="label" translatable="yes">{}</attribute>
      </item>
      <item>
        <attribute name="action">win.save</attribute>
        <attribute name="label" translatable="yes">{}</attribute>
      </item>
      <item>
        <attribute name="action">win.saveas</attribute>
        <attribute name="label" translatable="yes">{}</attribute>
      </item>
      <item>
        <attribute name="action">win.print</attribute>
        <attribute name="label" translatable="yes">{}</attribute>
      </item>
      <item>
        <attribute name="action">win.settings</attribute>
        <attribute name="label" translatable="yes">{}</attribute>
      </item>
      <item>
        <attribute name="action">win.about</attribute>
        <attribute name="label" translatable="yes">{}</attribute>
      </item>
      <item>
        <attribute name="action">win.quit</attribute>
        <attribute name="label" translatable="yes">{}</attribute>
    </item>
    </section>
  </menu>
</interface>
""".format(_lang.NEWFILE, _lang.FOPEN, _lang.FSAVE, _lang.FSAVEAS, _lang.FPRINT, _lang.FSETTINGS, _lang.ABOUT, _lang.QUIT)


class MainWindow(Adw.ApplicationWindow):
    # _files: list of gio.file - n_files its len
    def __init__(self, _files, n_files, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_default_size(WWIDTH, WHEIGHT)
        self.app_ = self.get_application()
        self.connect("close-request", self.on_this_close)
        try:
            self.connect("force-close", self.on_this_close)
        except:
            pass
        self.connect("destroy", self.on_this_close)
        # self.set_show_menubar(True)
        self.set_title(ENAME)
        global self_main
        self_main = self
        #
        self.css_provider = Gtk.CssProvider()
        self.css_provider.load_from_string("#texteditor.view {"+ \
"font-family: Monospace;"+ \
"font-size: {}pt;".format(FONT_SIZE)+"}")
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        #
        self.headerbar = Gtk.HeaderBar.new()
        self.headerbar.set_show_title_buttons(True)
        ### style manager
        self.style_manager = GtkSource.StyleSchemeManager.get_default()
        self._scheme = None
        if STYLE_SCHEME in self.style_manager.get_scheme_ids():
            self._scheme = self.style_manager.get_scheme(STYLE_SCHEME)
        ### language manager
        self.language_manager = GtkSource.LanguageManager.get_default()
        self._language = None
        l_languages = self.language_manager.get_language_ids()
        if LANGUAGE_STYLE in l_languages:
            self._language = self.language_manager.get_language(LANGUAGE_STYLE)
        #
        # left headerbar box
        self.lhbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.headerbar.pack_start(self.lhbox)
        #
        # right headerbar box
        self.rhbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.headerbar.pack_end(self.rhbox)
        # hamburger menu
        self.ham_menu = Gtk.MenuButton.new()
        if icon_theme.has_icon("open-menu-symbolic"):
            self.ham_menu.set_icon_name("open-menu-symbolic")
        elif icon_theme.has_icon("application-menu"):
            self.ham_menu.set_icon_name("application-menu")
        self.rhbox.append(self.ham_menu)
        # popover menu
        self.ham_pop = Gtk.Popover.new()
        self.ham_pop.set_has_arrow(False)
        self.ham_pop.set_halign(Gtk.Align.START)
        self.ham_menu.set_popover(self.ham_pop)
        # nothing
        self.ham_pop.connect("closed", self.on_popover_hammenu_closed)
        ## menu - actions
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self.on_quit_action_actived)
        self.add_action(quit_action)
        #
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about_action_actived)
        self.add_action(about_action)
        #
        settings_action = Gio.SimpleAction.new("settings", None)
        settings_action.connect("activate", self.on_settings_action)
        self.add_action(settings_action)
        #
        print_action = Gio.SimpleAction.new("print", None)
        print_action.connect("activate", self.on_print_action)
        self.add_action(print_action)
        #
        save_as_action = Gio.SimpleAction.new("saveas", None)
        save_as_action.connect("activate", self.on_save_as_action_actived)
        self.add_action(save_as_action)
        #
        save_action = Gio.SimpleAction.new("save", None)
        save_action.connect("activate", self.on_save_action_actived)
        self.add_action(save_action)
        #
        open_action = Gio.SimpleAction.new("open", None)
        open_action.connect("activate", self.on_open_action)
        self.add_action(open_action)
        #
        new_action = Gio.SimpleAction.new("new", None)
        new_action.connect("activate", self.on_new_action)
        self.add_action(new_action)
        #
        menu = Gtk.Builder.new_from_string(MENU_XML, -1).get_object("app-menu")
        self.ham_menu.set_menu_model(menu)
        #
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_content(self.main_box)
        self.main_box.append(self.headerbar)
        #
        self.editor_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.main_box.append(self.editor_box)
        #
        self._notebook = Gtk.Notebook.new()
        self._notebook.set_focusable(False)
        self._notebook.set_scrollable(True)
        self.editor_box.append(self._notebook)
        #
        if _files and _files != []:
            for _f in _files:
                sw = ScrolWin(self, _f)
                self._notebook.append_page(sw, sw.tab_label)
                self._notebook.set_tab_reorderable(sw, True)
                sw.text_editor.grab_focus()
                if self._scheme:
                    sw.buffer.set_style_scheme(self._scheme)
                if self._language:
                    sw.buffer.set_language(self._language)
        else:
            self.open_a_new_file(None)
        #
        # self._notebook.connect("switch-page", self.on_notebook_switch_page)
        # self._notebook.connect("change-current-page", self.on_notebook_change_page)
        
    # def on_notebook_switch_page(self, _notebook, _sw, i_sw):
        # text_searched = _sw._entry_entry
        
    # def on_notebook_change_page(self, _notebook, i_sw):
        # _sw = _notebook.get_nth_page(i_sw)
        # text_searched = _sw._entry_entry
    
    def set_font_size(self, _type):
        self.css_provider.load_from_string("#texteditor.view {"+ \
"font-family: Monospace;"+ \
"font-size: {}pt;".format(FONT_SIZE)+"}")
        Gtk.StyleContext.remove_provider_for_display(Gdk.Display.get_default(),self.css_provider)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
    def open_a_new_file(self, _file):
        sw = ScrolWin(self, _file)
        if sw.cannot_open == -1:
            return -1
        self._notebook.append_page(sw, sw.tab_label)
        self._notebook.set_tab_reorderable(sw, True)
        sw.text_editor.grab_focus()
        if self._scheme:
            sw.buffer.set_style_scheme(self._scheme)
        if self._language:
            sw.buffer.set_language(self._language)
        return 0
    
    def on_new_action(self, action, param=None):
        ret = self.open_a_new_file(None)
        if ret == -1:
            return
        self._notebook.set_current_page(-1)
    
    def on_open_action(self, action, param=None):
        _fd = Gtk.FileDialog.new()
        _fd.set_modal(True)
        _sw = self._notebook.get_nth_page(self._notebook.get_current_page())
        if _sw._file != None:
            _fd.set_initial_folder(Gio.File.new_for_path(os.path.dirname(_sw._file)))
        else:
            _fd.set_initial_folder(Gio.File.new_for_path(_HOME))
        # _filter = Gtk.FileFilter.new()
        # _filter.add_pattern("*.txt")
        # _fd.set_default_filter(_filter)
        def open_callback(source_object, res, data):
            try:
                l_gfile = _fd.open_text_file_finish(res)
                _file = l_gfile[0].get_path()
                if os.access(_file, os.R_OK):
                    ret = self.open_a_new_file(l_gfile[0])
                    if ret == 0:
                        self._notebook.set_current_page(-1)
            except GLib.GError as e:
                return
        try:
            _fd.open_text_file(self, None, open_callback, None)
        except Exception as E:
            AlDial(self_main, str(E))
    
    def on_popover_hammenu_closed(self, _w):
        _sw = self._notebook.get_current_page().sw
        _sw.text_editor.grab_focus()
    
    def on_scheme_changed(self, _btn, _param):
        for i in range(self._notebook.get_n_pages()):
            _sw = self._notebook.get_nth_page(i)
            _tb = _sw.buffer
            _scheme = _btn.get_style_scheme()
            _tb.set_style_scheme(_scheme)
            STYLE_SCHEME = _scheme.get_name()
        
    def on_save_action_actived(self, action, param=None):
        _sw = self._notebook.get_nth_page(self._notebook.get_current_page())
        if _sw._gfile == None:
            self.on_save_as_action_actived(action, param)
            return
        _tb = _sw.buffer
        is_buffer_modified = _tb.get_modified()
        _file_path = _sw._file
        try:
            with open(_file_path, "w") as _f:
                s_iter = _sw.buffer.get_iter_at_offset(0)
                e_iter = _sw.buffer.get_iter_at_offset(-1)
                b_text = _sw.buffer.get_text(s_iter, e_iter, True)
                _f.write(b_text)
                #
                # if is_buffer_modified:
                _tb.set_modified(False)
                _sw._lbl.set_label(os.path.basename(_sw._file))
                _sw.is_buffer_modified = False
                AlDial(self_main, _lang.FSAVED)
        except Exception as E:
            AlDial(self_main, str(E))
        _sw.text_editor.grab_focus()
        
    def on_save_as_action_actived(self, action, param=None):
        _fd = Gtk.FileDialog.new()
        _fd.set_modal(True)
        _sw = self._notebook.get_nth_page(self._notebook.get_current_page())
        if _sw._file != None:
            _fd.set_initial_folder(Gio.File.new_for_path(os.path.dirname(_sw._file)))
        else:
            _fd.set_initial_folder(Gio.File.new_for_path(_HOME))
        # _filter = Gtk.FileFilter.new()
        # _filter.add_pattern("*.txt")
        # _fd.set_default_filter(_filter)
        # # _fd.set_initial_name()
        def save_callback(source_object, res, data):
            _sw = self._notebook.get_nth_page(self._notebook.get_current_page())
            _tb = _sw.buffer
            is_buffer_modified = _tb.get_modified()
            _file_path = _sw._file
            try:
                # the real file name
                _gfile = _fd.save_text_file_finish(res)
                if is_buffer_modified:
                    _tb.set_modified(False)
                #
                _sw._gfile = _gfile[0]
                _sw._file = _gfile[0].get_path()
                _sw._lbl.set_label(os.path.basename(_sw._file))
                _sw.is_buffer_modified = False
            except GLib.GError as e:
                return
            #
            if _gfile is not None:
                _file_path = _gfile[0].get_path()
                try:
                    with open(_file_path, "w") as _f:
                        s_iter = _sw.buffer.get_iter_at_offset(0)
                        e_iter = _sw.buffer.get_iter_at_offset(-1)
                        b_text = _sw.buffer.get_text(s_iter, e_iter, True)
                        _f.write(b_text)
                        AlDial(self_main, _lang.FSAVED)
                        _sw.text_editor.grab_focus()
                        if _sw.file_is_monitored == False:
                            # _sw.set_monitor_file()
                            GLib.idle_add(_sw.set_monitor_file)
                except Exception as E:
                    AlDial(self_main, str(E))
        try:
            _fd.save_text_file(self, None, save_callback, None)
        except Exception as E:
            AlDial(self_main, str(E))
        
    def on_print_action(self, action, param=None):
        _sw = self._notebook.get_nth_page(self._notebook.get_current_page())
        _file = _sw._file
        _name = os.path.basename(_file)
        #
        _editor = _sw.text_editor
        #
        font_desc = _editor.get_pango_context().get_font_description()
        if font_desc:
            size = font_desc.get_size() / 1024
            size = PRINTER_FONT_SIZE
            font_desc.set_size(int(size * 1024))
            font_name = font_desc.to_string()
        #
        _compositor = GtkSource.PrintCompositor.new_from_view(_editor)
        _compositor.set_wrap_mode(Gtk.WrapMode.CHAR)
        _compositor.set_highlight_syntax(False)
        _compositor.set_print_line_numbers(False)
        _compositor.set_body_font_name(font_name)
        #
        print_operation = Gtk.PrintOperation()
        print_operation.set_show_progress(True)
        print_operation.connect("begin-print", self.on_begin_print, _compositor)
        print_operation.connect("draw-page", self.on_draw_page, _compositor)
        print_operation.connect("done", self.on_print_done, _name)
        #
        res = print_operation.run(
            Gtk.PrintOperationAction.PRINT_DIALOG,
            self.app_.get_active_window())
        #
        # if res == Gtk.PrintOperationResult.ERROR:
            # AlDial(self_main, "{}: {}".format(_lang.FPRINTEDERROR, _name))
        # elif res == Gtk.PrintOperationResult.APPLY:
            # AlDial(self_main, "{}: {}".format(_lang.FPRINTED, _name))
        
    def on_print_done(self, print_operation, res, _name):
        if res == Gtk.PrintOperationResult.ERROR:
            AlDial(self_main, "{}: {}".format(_lang.FPRINTEDERROR, _name))
        elif res == Gtk.PrintOperationResult.APPLY:
            AlDial(self_main, "{}: {}".format(_lang.FPRINTED, _name))
        
    def on_begin_print(self, operation, context, compositor):
        while not compositor.paginate(context):
            pass
        n_pages = compositor.get_n_pages()
        operation.set_n_pages(n_pages)

    def on_draw_page(self, operation, context, page_nr, compositor):
        compositor.draw_page(context, page_nr)
    
    def dialog_action(self, _obj, _res, _data=None):
        _result = _obj.choose_finish(_res)
        if _result == "0":
            if SINGLE_APP == 0:
                self.app_.quit()
            else:
                self.destroy()
        else:
            return
    
    def on_quit_action_actived(self, action, param=None):
        n_pages = self._notebook.get_n_pages()
        files_to_save = ""
        for i in range(n_pages):
            _sw = self._notebook.get_nth_page(i)
            if _sw.buffer.get_modified():
                files_to_save += os.path.basename(_sw._file)+"\n"
        if files_to_save != "":
            YNDial(self, _lang.FILESTOSAVE, files_to_save+"\n"+_lang.FCLOSEANYWAY)
        else:
            if SINGLE_APP == 0:
                self.app_.quit()
            else:
                self.destroy()
    
    def on_this_close(self, _w):
        global WWIDTH
        global WHEIGHT
        _WWIDTH = self.get_width()
        _WHEIGHT = self.get_height()
        if _WWIDTH != WWIDTH or _WHEIGHT != WHEIGHT:
            WWIDTH = _WWIDTH
            config_conf["wwidth"] = WWIDTH
            WHEIGHT = _WHEIGHT
            config_conf["wheight"] = WHEIGHT
            try:
                _ff =  open(os.path.join(HOME_CONFIG,"configs/config.json"), "w")
                json.dump(config_conf, _ff, indent = 4)
                _ff.close()
            except:
                pass
        self.on_quit_action_actived(None)
        return True
        
    def on_settings_action(self, action, param=None):
        WinSettings(self)
    
    def on_about_action_actived(self, action, param=None):
        _aboutdial = Adw.AboutDialog.new()
        _aboutdial.set_presentation_mode(Adw.DialogPresentationMode.FLOATING)#.BOTTOM_SHEET)#.FLOATING)
        _aboutdial.set_application_icon("com.zephyr.text.editor")
        _aboutdial.set_developers(["Philip J. Fry"])
        _aboutdial.set_comments("Made for me 🙂")
        _aboutdial.set_version(VERSION)
        _aboutdial.set_website(ESITE)
        _aboutdial.set_license_type(Gtk.License.GPL_3_0_ONLY)
        _aboutdial.present(self)


# class ScrolWin(Gtk.ScrolledWindow):
class ScrolWin(Gtk.Box):
    def __init__(self, _parent, _gfile):
        super().__init__()
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.main_app = _parent
        self._gfile = _gfile
        self._file = None
        self._entry_entry = ""
        self._nfile = _lang.FNEWFILE
        if _gfile == None:
            the_new_file = os.path.join(_HOME, _lang.FNEWFILE)
            while os.path.exists(the_new_file):
                the_new_file += "_1"
            else:
                self._nfile = os.path.basename(the_new_file)
                self._file = the_new_file
        #
        self.set_hexpand(True)
        self.set_vexpand(True)
        ## find function
        self.find_box = Gtk.Box.new(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.find_box.set_margin_start(4)
        self.find_box.set_margin_end(4)
        self.find_box.set_margin_top(4)
        self.find_box.set_margin_bottom(4)
        self.append(self.find_box)
        self.find_box.set_visible(False)
        #
        self.sw = Gtk.ScrolledWindow.new()
        self.sw.set_hexpand(True)
        self.sw.set_vexpand(True)
        self.sw.propagate_natural_height = 1
        self.sw.propagate_natural_width = 1
        self.append(self.sw)
        #
        self.search_entry = Gtk.Entry.new()
        self.search_entry.set_hexpand(True)
        self.search_entry.connect("activate", self.on_search_entry_activate)
        self.search_entry.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "search")
        self.search_entry.connect("icon-press", self.on_search_icon_pressed)
        self.find_box.append(self.search_entry)
        self.search_buffer = self.search_entry.get_buffer()
        self.match_start = -1
        self.match_end = -1
        #
        self.hl_all = Gtk.ToggleButton(label=_lang.HLALL)
        self.hl_all.connect("toggled", self.on_highlight_all)
        self.find_box.append(self.hl_all)
        #
        self.prev_btn = Gtk.Button(label=_lang.PREV)
        self.prev_btn.connect("clicked", self.on_btn_search, -1)
        self.find_box.append(self.prev_btn)
        #
        self.next_btn = Gtk.Button(label=_lang.NEXT)
        self.next_btn.connect("clicked", self.on_btn_search, 1)
        self.find_box.append(self.next_btn)
        #
        self.text_editor = GtkSource.View.new()
        self.text_editor.set_hexpand(True)
        self.text_editor.set_vexpand(True)
        self.text_editor.set_name("texteditor")
        self.text_editor.set_monospace(True)
        self.text_editor.set_show_line_numbers(True)
        self.text_editor.set_show_right_margin(True)
        # self.text_editor.set_right_margin_position(80)
        self.text_editor.set_highlight_current_line(True)
        self.text_editor.set_indent_on_tab(True)
        if TAB_SIZE != 0:
            self.text_editor.set_indent_width(TAB_SIZE_LIST[TAB_SIZE])
            self.text_editor.set_insert_spaces_instead_of_tabs(True)
        self.text_editor.set_auto_indent(True)
        self.text_editor.set_smart_backspace(True)
        #
        self.EDITABLE = 1
        self.text_editor.set_editable(self.EDITABLE)
        #
        self.WRAP_MODE = 0
        self.text_editor.set_wrap_mode(self.WRAP_MODE)
        self.text_editor.set_smart_home_end(GtkSource.SmartHomeEndType.BEFORE)
        self.sw.set_child(self.text_editor)
        self.is_buffer_modified = False
        self.file_reloaded = False
        #
        self.buffer = self.text_editor.get_buffer()
        self.buffer.set_highlight_syntax(True)
        #
        # self.text_editor.set_show_line_marks(True)
        # self.text_editor.set_enable_snippets(True)
        # self.completion = self.text_editor.get_completion()
        # self.c_provider = GtkSource.CompletionWords.new("compl")
        # self.c_provider.register(self.buffer)
        # self.completion.add_provider(self.c_provider) 
        #
        self.file_is_monitored = False
        self.monitor_file = None
        self.cannot_open = 0
        if self._gfile != None:
            self._file = self._gfile.get_path()
            _text = ""
            try:
                _f = open(self._file, "r")
                _text = _f.read()
                _f.close()
                self.buffer.set_text(_text, -1)
                self.buffer.set_modified(False)
                self.on_create_notebook_label(self._file)
                self.set_monitor_file()
            except Exception as E:
                # self.buffer.set_text("", -1)
                # self.on_create_notebook_label(None)
                AlDial(self_main, self._file+"\n\n"+str(E))
                self.cannot_open = -1
                return None
        else:
            self.on_create_notebook_label(None)
        #
        self.buffer.connect("changed", self.tbuffer_changed)
        self.connection_modified = self.buffer.connect("modified-changed", self.tbuffer_modified_changed)
        _color_back = Gdk.RGBA()
        _color_back.parse(HLBACKGROUND)
        _color_fore = Gdk.RGBA()
        _color_fore.parse(HLFOREGROUND)
        self.tag_found = self.buffer.create_tag("found", background_rgba=_color_back, foreground_rgba=_color_fore)
        #
        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        key_ctrl.connect("key-pressed", self.on_key_pressed)
        self.add_controller(key_ctrl)
        #
        self._extra_menu = self.text_editor.get_extra_menu()
        button_reload = Gio.SimpleAction(name="Reload", parameter_type=None, enabled=True)
        button_reload.connect("activate", self.on_file_reload)
        reload_menu_item = Gio.MenuItem.new(_lang.FRELOAD, "win.Reload")
        self._extra_menu.append(_lang.FRELOAD, "win.Reload")
        self.main_app.add_action(button_reload)
        #
        if SINGLE_APP == 0:# and self.main_app._notebook.get_n_pages() > 0:
            button_detach = Gio.SimpleAction(name="Detach", parameter_type=None, enabled=True)
            button_detach.connect("activate", self.on_file_detach)
            reload_menu_item = Gio.MenuItem.new(_lang.FDETACH, "win.Reload")
            self._extra_menu.append(_lang.FDETACH, "win.Detach")
            self.main_app.add_action(button_detach)
        #
        if self._file == None:
            AlDial(self_main, _lang.FMESSAGE)
            self.main_app.app_.quit()
    
    def set_monitor_file(self):
        if FILE_MONITORING == 1:
            self.monitor_file = self._gfile.monitor_file(Gio.FileMonitorFlags.SEND_MOVED|Gio.FileMonitorFlags.WATCH_MOVES, None)
            self.monitor_file.connect("changed", self.on_file_changed)
            self.file_is_monitored = True
    
    def on_file_changed(self, file_monitor, file, other_file, event_type):
        if event_type == Gio.FileMonitorEvent.CHANGED:
            AlDial(self_main, "File changed: {}".format(self._file))
            self.buffer.set_modified(True)
        elif event_type == Gio.FileMonitorEvent.RENAMED or event_type == Gio.FileMonitorEvent.MOVED:
            AlDial(self_main, "File renamed: {}".format(self._file))
            self.buffer.set_modified(True)
        elif event_type == Gio.FileMonitorEvent.DELETED:
            AlDial(self_main, "File deleted: {}".format(self._file))
            self.buffer.set_modified(True)
    
    def on_search_icon_pressed(self, _e, _pos):
        self.search_buffer.set_text("", -1)
        s_iter = self.buffer.get_iter_at_offset(0)
        e_iter = self.buffer.get_iter_at_offset(-1)
        self.buffer.remove_tag(self.tag_found, s_iter, e_iter)
        self._entry_entry = ""
        self.next_btn.set_sensitive(True)
        self.prev_btn.set_sensitive(True)
        self.hl_all.set_active(False)
    
    def on_search_entry_activate(self, _e=None, _d=1):
        self.match_start = -1
        self.match_end = -1
        text_searched = self.search_buffer.get_text()
        self._entry_entry = text_searched
        #
        start = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        if start.get_offset() == self.buffer.get_char_count():
            start = self.buffer.get_start_iter()
        self.search_and_mark(text_searched, start, None,  _d)
        
    def search_and_mark(self, text, start, end, _t):
        if _t == 1:
            match = start.forward_search(text, Gtk.TextSearchFlags.CASE_INSENSITIVE, None) # end) # useless?
        elif _t == -1:
            match = start.backward_search(text, Gtk.TextSearchFlags.CASE_INSENSITIVE, None)
        if match == None and _t == 1:
            start = self.buffer.get_start_iter()
            end = self.buffer.get_end_iter()
            match = start.forward_search(text, Gtk.TextSearchFlags.CASE_INSENSITIVE, None)
        elif match == None and _t == -1:
            start = self.buffer.get_end_iter()
            match = start.backward_search(text, Gtk.TextSearchFlags.CASE_INSENSITIVE, None)
        if match is not None:
            ### remove the tag before
            s_iter = self.buffer.get_iter_at_offset(0)
            e_iter = self.buffer.get_iter_at_offset(-1)
            self.buffer.remove_tag(self.tag_found, s_iter, e_iter)
            #
            self.match_start, self.match_end = match
            self.buffer.apply_tag(self.tag_found, self.match_start, self.match_end)
            # scroll the view
            self.text_editor.scroll_to_iter(self.match_end, 0.2, False, 0, 0)
            
    def on_highlight_all(self, _w):
        text = self.search_buffer.get_text()
        if text == "":
            _w.set_active(False)
            return
        if _w.get_active():
            self.next_btn.set_sensitive(False)
            self.prev_btn.set_sensitive(False)
            text = self.search_buffer.get_text()
            cursor_mark = self.buffer.get_insert()
            start = self.buffer.get_iter_at_mark(cursor_mark)
            if start.get_offset() == self.buffer.get_char_count():
                start = self.buffer.get_start_iter()
            self.search_and_mark_all(text, start)
        else:
            self.next_btn.set_sensitive(True)
            self.prev_btn.set_sensitive(True)
            s_iter = self.buffer.get_iter_at_offset(0)
            e_iter = self.buffer.get_iter_at_offset(-1)
            self.buffer.remove_tag(self.tag_found, s_iter, e_iter)
        
    def search_and_mark_all(self, text, start):
        end = self.buffer.get_end_iter()
        match = start.forward_search(text, 0, end)
        if match is not None:
            match_start, match_end = match
            self.buffer.apply_tag(self.tag_found, match_start, match_end)
            self.search_and_mark_all(text, match_end)
            
    def on_btn_search(self, _w, _t):
        text = self.search_buffer.get_text()
        if self.match_start == -1 and self.match_end == -1:
            self.on_search_entry_activate(None, _t)
            return
        if _t == 1:
            self.search_and_mark(text, self.match_end, None, 1)
        elif _t == -1:
            self.search_and_mark(text, self.match_start, None, -1)
    
    def tbuffer_modified_changed(self, _tb):
        if self.file_reloaded == True:
            self.file_reloaded = False
            return
        if self.is_buffer_modified == False:
            self._lbl.set_label(self._lbl.get_label()+" *")
            self.is_buffer_modified = True
    
    def on_file_reload(self, action, param):
        try:
            _f = open(self._file, "r")
            _text = _f.read()
            _f.close()
            self.file_reloaded = True
            self.buffer.set_text(_text, -1)
            self.buffer.set_modified(False)
        except Exception as E:
            AlDial(self_main, str(E))
        
    def on_file_detach(self, action, param):
        if self.main_app._notebook.get_n_pages() == 1:
            return
        if self.buffer.get_modified() == True:
            AlDial(self_main, _lang.FILESAVEFIRSTDETACH)
            return
        try:
            _cp = self.main_app._notebook.get_current_page()
            if os.path.exists("/usr/bin/ZephyrTE.sh"):
                _prog = "/usr/bin/ZephyrTE.sh"
                _cwd = _curr_dir
            else:
                _prog = os.path.join(_curr_dir, "ZephyrTE.sh")
                _cwd = "/usr/bin"
            subprocess.Popen([_prog, "-t", self._file], cwd=_cwd)
            self.main_app._notebook.remove_page(_cp)
        except Exception as E:
            AlDial(self_main, str(E))
        
    def on_key_pressed(self, ctrl, keyval, keycode, state):
        if self._autoclose_signs == 1: # 1
            if getattr(self.buffer, "_is_loading", False):
                return True
            _c = Gdk.keyval_to_unicode(keyval)
            if chr(_c) in SIGN_AUTOCLOSE_LIST:
                _cn = SIGN_AUTOCLOSE_LIST_NEXT[SIGN_AUTOCLOSE_LIST.index(chr(_c))]
                self.buffer.insert_at_cursor(_cn)
                insert_mark = self.buffer.get_insert()
                iter = self.buffer.get_iter_at_mark(insert_mark)
                iter.backward_char()
                self.buffer.place_cursor(iter)
        return False
        
    def tbuffer_changed(self, _tb):
        if self.file_reloaded == True:
            return
        if self.is_buffer_modified == False:
            self._lbl.set_label(self._lbl.get_label()+" *")
            self.is_buffer_modified = True
    
    def on_close_this(self, w):
        if self.main_app._notebook.get_n_pages() > 1:
            if self.monitor_file:
                self.monitor_file.cancel()
            idx = self.main_app._notebook.get_current_page()
            self.main_app._notebook.remove_page(idx)
    
    def on_editable_btn(self, _w):
        _state = _w.get_active()
        self.EDITABLE = _state
        self.text_editor.set_editable(_state)
        self.text_editor.grab_focus()
        
    def on_wrap_btn(self, _w):
        _state = _w.get_active()
        self.WRAP_MODE = _state
        self.text_editor.set_wrap_mode(_state)
        self.text_editor.grab_focus()
        
    def on_autoclose_btn(self, _w):
        self._autoclose_signs = not self._autoclose_signs
        self.text_editor.grab_focus()
        
    def on_find_show(self, _w):
        if _w.get_active():
            self.find_box.set_visible(True)
            self.next_btn.set_sensitive(True)
            self.prev_btn.set_sensitive(True)
            self.hl_all.set_active(False)
        else:
            s_iter = self.buffer.get_iter_at_offset(0)
            e_iter = self.buffer.get_iter_at_offset(-1)
            self.buffer.remove_tag(self.tag_found, s_iter, e_iter)
            self.find_box.set_visible(False)
        
    def on_create_notebook_label(self, _file):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        # editable button
        self.editable_btn = Gtk.ToggleButton.new()
        _btn_il = None
        if icon_theme.has_icon("edit-symbolic"):
            _btn_il = "edit-symbolic"
        elif icon_theme.has_icon("edit"):
            _btn_il = "edit"
        elif icon_theme.has_icon("edittext"):
            _btn_il = "edittext"
        elif icon_theme.has_icon("gtk-edit"):
            _btn_il = "gtk-edit"
        if _btn_il:
            self.editable_btn.set_icon_name(_btn_il)
        self.editable_btn.set_tooltip_text(_lang.EDITABLE)
        self.editable_btn.set_active(self.EDITABLE)
        self.editable_btn.connect("toggled", self.on_editable_btn)
        box.append(self.editable_btn)
        # wrap
        self.wrap_btn = Gtk.ToggleButton.new()
        _btn_il = None
        if icon_theme.has_icon("gtk-justify-fill"):
            _btn_il = "gtk-justify-fill"
        elif icon_theme.has_icon("format-justify-fill"):
            _btn_il = "format-justify-fill"
        elif icon_theme.has_icon("format-indent-less"):
            _btn_il = "format-indent-less"
        elif icon_theme.has_icon("gtk-indent-ltr"):
            _btn_il = "gtk-indent-ltr"
        if _btn_il:
            self.wrap_btn.set_icon_name(_btn_il)
        self.wrap_btn.set_tooltip_text(_lang.WRAPMODE)
        self.wrap_btn.set_active(self.WRAP_MODE)
        self.wrap_btn.connect("toggled", self.on_wrap_btn)
        box.append(self.wrap_btn)
        # autoclose
        self.autoclose_btn = Gtk.ToggleButton.new()
        _btn_il = None
        if icon_theme.has_icon("format-text-code"):
            _btn_il = "format-text-code"
        elif icon_theme.has_icon("dialog-xml-editor"):
            _btn_il = "dialog-xml-editor"
        elif icon_theme.has_icon("dialog-layers"):
            _btn_il = "dialog-layers"
        elif icon_theme.has_icon("gtk-fullscreen"):
            _btn_il = "gtk-fullscreen"
        if _btn_il:
            self.autoclose_btn.set_icon_name(_btn_il)
        self.autoclose_btn.set_tooltip_text(_lang.AUTOCLOSE)
        self.autoclose_btn.set_active(SIGN_AUTOCLOSE)
        self.autoclose_btn.connect("toggled", self.on_autoclose_btn)
        box.append(self.autoclose_btn)
        self._autoclose_signs = SIGN_AUTOCLOSE
        # find
        self.find_btn = Gtk.ToggleButton.new()
        if icon_theme.has_icon("edit-find"):
            fnd_il = "edit-find"
        elif icon_theme.has_icon("find"):
            fnd_il = "find"
        elif icon_theme.has_icon("edit-find-replace"):
            fnd_il = edit-find-replace
        elif icon_theme.has_icon("system-search"):
            fnd_il = "system-search"
        self.find_btn.set_icon_name(fnd_il)
        self.find_btn.set_tooltip_text(_lang.FINDTOOLTIP)
        self.find_btn.connect("toggled", self.on_find_show)
        box.append(self.find_btn)
        # 
        if _file:
            self._lbl = Gtk.Label(label=os.path.basename(_file))
        else:
            self._lbl = Gtk.Label(label=self._nfile) # page label
        box.set_tooltip_text(_file)
        self._lbl.set_hexpand(True)
        box.append(self._lbl)
        self._label_tab = self._lbl
        # close button
        btn = Gtk.Button.new()
        if icon_theme.has_icon("gtk-close"):
            _btn_il = "gtk-close"
        elif icon_theme.has_icon("stock-close"):
            _btn_il = "stock-close"
        elif icon_theme.has_icon("close"):
            _btn_il = "close"
        elif icon_theme.has_icon("window-close"):
            _btn_il = "window-close"
        btn.set_icon_name(_btn_il)
        btn.connect("clicked", self.on_close_this)
        box.append(btn)
        self.tab_label = box

class AlDial(Adw.AlertDialog):
    def __init__(self, _parent, _str1):
        super().__init__()
        self._parent = _parent
        self._str1 = _str1
        self.set_body(self._str1)
        self.add_response("close", _lang.CLOSE)
        self.connect("response", self.on_close)
        self.present(self_main)
        
    def on_close(self, _d, _r):
        self.close()

# yes/no dialog - close the application and check for files modified
class YNDial(Adw.AlertDialog):
    def __init__(self, _parent, _str1, _str2):
        super().__init__()
        self._parent = _parent
        self._str1 = _str1
        self._str2 = _str2
        #
        self.add_response("0", _lang.YES)
        self.add_response("1", _lang.NO)
        self.set_heading(self._str1)
        self.set_body(self._str2)
        #
        self.choose(self._parent, None, self._parent.dialog_action, None)

##################

class WinSettings(Adw.Dialog):
    def __init__(self, _parent):
        super().__init__()
        self._parent = _parent
        self.set_name("settingdialog")
        self.set_size_request(800, 300)
        self.set_title(_lang.FSETTINGS)
        #
        self.headerbar = Gtk.HeaderBar.new()
        self.headerbar.set_show_title_buttons(False)
        headerbar_lbl = Gtk.Label(label="<b>"+_lang.FSETTINGS+"</b>")
        headerbar_lbl.set_use_markup(True)
        self.headerbar.set_title_widget(headerbar_lbl)
        #
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(self.main_box)
        self.main_box.append(self.headerbar)
        #
        self.stack_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.main_box.append(self.stack_box)
        #
        self.stack_sidebar = Gtk.StackSidebar.new()
        self.stack_sidebar.set_vexpand(True)
        self.stack_box.append(self.stack_sidebar)
        #
        btn_apply = Gtk.Button(label=_lang.APPLY)
        btn_apply.connect("clicked", self.on_apply)
        btn_apply.set_css_classes(["suggested-action",""])
        self.headerbar.pack_start(btn_apply)
        #
        btn_close = Gtk.Button(label=_lang.CLOSE)
        btn_close.connect("clicked", self.on_close)
        self.headerbar.pack_end(btn_close)
        #
        self._stack = Gtk.Stack.new()
        self._stack.props.hexpand = True
        self._stack.props.vexpand = True
        self.stack_sidebar.set_stack(self._stack)
        self.stack_box.append(self._stack)
        ############
        box1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._stack.add_titled(box1,"box1",_lang.PGENERAL)
        bgrid1 = Gtk.Grid.new()
        bgrid1.set_column_homogeneous(False)
        bgrid1.set_hexpand(True)
        bgrid1.set_vexpand(True)
        box1.append(bgrid1)
        # font size
        lbl00 = Gtk.Label(label=_lang.FONTSIZE)
        lbl00.set_halign(Gtk.Align.START)
        bgrid1.attach(lbl00,0,0,1,1)
        self.fontsize_spinbtn = Gtk.SpinButton.new_with_range(4,80,1)
        self.fontsize_spinbtn.set_value(FONT_SIZE)
        bgrid1.attach_next_to(self.fontsize_spinbtn,lbl00,1,1,1)
        # use the rubberband
        lbl01 = Gtk.Label(label=_lang.STYLESHEME)
        lbl01.set_halign(Gtk.Align.START)
        bgrid1.attach(lbl01,0,1,1,1)
        self._schemes = self._parent.style_manager.get_scheme_ids()
        self.stylescheme_combo = Gtk.DropDown.new_from_strings(self._schemes)
        if STYLE_SCHEME in self._schemes:
            self.stylescheme_combo.set_selected(self._schemes.index(STYLE_SCHEME))
        bgrid1.attach_next_to(self.stylescheme_combo,lbl01,1,1,1)
        # language style
        lbl02 = Gtk.Label(label=_lang.LANGUAGE)
        lbl02.set_halign(Gtk.Align.START)
        bgrid1.attach(lbl02,0,2,1,1)
        self._languages = self._parent.language_manager.get_language_ids()
        self._languages.insert(0, _lang.LDEFAULT)
        self.language_combo = Gtk.DropDown.new_from_strings(self._languages)
        if LANGUAGE_STYLE in self._languages:
            self.language_combo.set_selected(self._languages.index(LANGUAGE_STYLE))
        bgrid1.attach_next_to(self.language_combo,lbl02,1,1,1)
        self.restore_lang = Gtk.Button(label=_lang.RESTORELANG)
        def on_restore_language(_w):
            global LANGUAGE_STYLE
            LANGUAGE_STYLE = ""
            self.language_combo.set_selected(0)
        self.restore_lang.connect("clicked", on_restore_language)
        bgrid1.attach_next_to(self.restore_lang,self.language_combo,1,1,1)
        # printer font size
        lbl03 = Gtk.Label(label=_lang.PFONTSIZE)
        lbl03.set_halign(Gtk.Align.START)
        bgrid1.attach(lbl03,0,3,1,1)
        self.printerfontsize_spinbtn = Gtk.SpinButton.new_with_range(0,40,1)
        self.printerfontsize_spinbtn.set_value(PRINTER_FONT_SIZE)
        bgrid1.attach_next_to(self.printerfontsize_spinbtn,lbl03,1,1,1)
        # tab size: 0 use tab, or 2,4,8 spaces
        lbl04 = Gtk.Label(label=_lang.TABSIZE)
        lbl04.set_halign(Gtk.Align.START)
        bgrid1.attach(lbl04,0,4,1,1)
        self.tabsize_combo = Gtk.DropDown.new_from_strings([_lang.TTAB,"2","4","8"])
        self.tabsize_combo.set_selected(TAB_SIZE)
        self.tabsize_combo.set_tooltip_text(_lang.TABONLYTHISVIEWORRESTART)
        bgrid1.attach_next_to(self.tabsize_combo,lbl04,1,1,1)
        # file_monitoring
        lbl05 = Gtk.Label(label=_lang.FILEMONITORING)
        lbl05.set_halign(Gtk.Align.START)
        bgrid1.attach(lbl05,0,5,1,1)
        self.file_monitoring = Gtk.DropDown.new_from_strings([_lang.NO, _lang.YES])
        self.file_monitoring.set_selected(FILE_MONITORING)
        bgrid1.attach_next_to(self.file_monitoring,lbl05,1,1,1)
        # single app
        lbl06 = Gtk.Label(label=_lang.SINGLEAPP)
        lbl06.set_halign(Gtk.Align.START)
        bgrid1.attach(lbl06,0,6,1,1)
        self.single_app = Gtk.DropDown.new_from_strings([_lang.NO, _lang.YES])
        self.single_app.set_selected(SINGLE_APP)
        bgrid1.attach_next_to(self.single_app,lbl06,1,1,1)
        ### highlight colours
        # background
        lbl07 = Gtk.Label(label=_lang.BACKGROUNDCOLOR)
        lbl07.set_halign(Gtk.Align.START)
        bgrid1.attach(lbl07,0,7,1,1)
        color_dlg = Gtk.ColorDialog.new()
        self.bcolor_btn = Gtk.ColorDialogButton.new(color_dlg)
        _btn_color = Gdk.RGBA()
        _btn_color.parse(HLBACKGROUND)
        self.bcolor_btn.set_rgba(_btn_color)
        bgrid1.attach_next_to(self.bcolor_btn,lbl07,1,1,1)
        # foreground
        lbl08 = Gtk.Label(label=_lang.FOREGROUNDCOLOR)
        lbl08.set_halign(Gtk.Align.START)
        bgrid1.attach(lbl08,0,8,1,1)
        color_dlg = Gtk.ColorDialog.new()
        self.fcolor_btn = Gtk.ColorDialogButton.new(color_dlg)
        _btn_color = Gdk.RGBA()
        _btn_color.parse(HLFOREGROUND)
        self.fcolor_btn.set_rgba(_btn_color)
        bgrid1.attach_next_to(self.fcolor_btn,lbl08,1,1,1)
        ########
        self.present(self._parent)
        
    def on_apply(self, w):
        global WWIDTH
        global WHEIGHT
        global PRINTER_FONT_SIZE
        global STYLE_SCHEME
        global LANGUAGE_STYLE
        global TAB_SIZE
        global SIGN_AUTOCLOSE
        global FILE_MONITORING
        global FONT_SIZE
        global SINGLE_APP
        global HLFOREGROUND
        global HLBACKGROUND
        _sw = self._parent._notebook.get_nth_page(self._parent._notebook.get_current_page())
        #
        WWIDTH = self._parent.get_width()
        config_conf["wwidth"] = self._parent.get_width()
        WHEIGHT = self._parent.get_height()
        config_conf["wheight"] = self._parent.get_height()
        PRINTER_FONT_SIZE = int(self.printerfontsize_spinbtn.get_value())
        config_conf["printer-font-size"] = PRINTER_FONT_SIZE
        #
        STYLE_SCHEME_TMP = self.stylescheme_combo.get_selected()
        try:
            STYLE_SCHEME = self._schemes[STYLE_SCHEME_TMP]
        except:
            pass
        config_conf["scheme"] = STYLE_SCHEME
        #
        LANGUAGE_STYLE_TMP = self.language_combo.get_selected()
        try:
            LANGUAGE_STYLE = self._languages[LANGUAGE_STYLE_TMP]
            if LANGUAGE_STYLE == _lang.LDEFAULT:
                _sw.buffer.set_language(None)
            else:
                _sw.buffer.set_language(LANGUAGE_STYLE)
        except:
            pass
        config_conf["language"] = LANGUAGE_STYLE
        #
        TAB_SIZE = self.tabsize_combo.get_selected()
        config_conf["tab-size"] = TAB_SIZE
        if TAB_SIZE != 0:
            _sw.text_editor.set_indent_width(TAB_SIZE_LIST[TAB_SIZE])
            _sw.text_editor.set_insert_spaces_instead_of_tabs(True)
        else:
            _sw = self._notebook.get_current_page_page()
            _sw.text_editor.set_insert_spaces_instead_of_tabs(False)
        #
        config_conf["autoclose-signs"] = SIGN_AUTOCLOSE
        #
        FILE_MONITORING = self.file_monitoring.get_selected()
        config_conf["file-monitoring"] = FILE_MONITORING
        #
        FONT_SIZE = int(self.fontsize_spinbtn.get_value())
        config_conf["font-size"] = FONT_SIZE
        self._parent.set_font_size(1)
        #
        SINGLE_APP = self.single_app.get_selected()
        config_conf["single-app"] = SINGLE_APP
        #
        HLFOREGROUND = self.fcolor_btn.get_rgba().to_string()
        config_conf["hlforeground"] = HLFOREGROUND
        HLBACKGROUND = self.bcolor_btn.get_rgba().to_string()
        config_conf["hlbackground"] = HLBACKGROUND
        _sw.tag_found.props.foreground_rgba = self.fcolor_btn.get_rgba()
        _sw.tag_found.props.background_rgba = self.bcolor_btn.get_rgba()
        #
        try:
            _ff =  open(os.path.join(HOME_CONFIG,"configs/config.json"), "w")
            json.dump(config_conf, _ff, indent = 4)
            _ff.close()
        except Exception as E:
            AlDial(self_main, str(E))
        #
        self.close()
        _sw.text_editor.grab_focus()
    
    def on_close(self, w):
        self.close()
        _sw = self._parent._notebook.get_nth_page(self._parent._notebook.get_current_page())
        _sw.text_editor.grab_focus()


class MyApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_main_option("single-instance",ord("t"),GLib.OptionFlags.NONE,GLib.OptionArg.NONE,"Single instance",None)
        self._files = None
        self.n_files = None
            
    def do_activate(self):
        active_window = self.props.active_window
        if active_window:
            active_window.present()
        else:
            self.win = MainWindow(application=self, _files=self._files, n_files=self.n_files)
            self.win.present()
    
    def do_open(self, _files, n_files, _data):
        active_window = self.props.active_window
        if SINGLE_APP == 0:
            if active_window:
                if n_files > 0:
                    file_found = 0
                    for _gf in _files:
                        # do not open files already open
                        n_pages = active_window._notebook.get_n_pages()
                        for i in range(n_pages):
                            __sw = active_window._notebook.get_nth_page(i)
                            if __sw._gfile and __sw._gfile.get_path() == _gf.get_path():
                                file_found = 1
                                break
                        #
                        if file_found == 1:
                            continue
                        #
                        _sw = ScrolWin(active_window, _gf)
                        idx = active_window._notebook.append_page(_sw, _sw.tab_label)
                        active_window._notebook.set_tab_reorderable(_sw, True)
                        active_window._notebook.set_current_page(idx)
                        _sw.text_editor.grab_focus()
                        #
                        if active_window._scheme:
                            _sw.buffer.set_style_scheme(active_window._scheme)
                        if active_window._language:
                            _sw.buffer.set_language(active_window._language)
                active_window.present()
            else:
                self._files = _files
                self.n_files = n_files
                self.activate()
        else:
            self.win = MainWindow(application=self, _files=_files, n_files=n_files)
            self.win.present()
    
    def do_command_line(self, command_line):
        active_window = self.props.active_window
        options = command_line.get_options_dict()
        options = options.end().unpack()
        if "single-instance" in options:
            args = command_line.get_arguments()
            COMMANDLINE_CWD = command_line.get_cwd()
            try:
                subprocess.Popen([os.path.join(COMMANDLINE_CWD,"ZephyrTE.sh"),args[1]])#, start_new_session=True)
            except:
                pass
            return 0
        else:
            args = command_line.get_arguments()
            _gfile = command_line.create_file_for_arg(args[-1])
            _files = [_gfile]
            n_files = 1
            if active_window:
                active_window.present()
            else:
                self.win = MainWindow(application=self, _files=_files, n_files=n_files)
                self.win.present()
        return 0

################
if "-t" in sys.argv or "--single-instance" in sys.argv:
    SINGLE_APP = 1
if SINGLE_APP == 1:
    app = MyApp(application_id="com.zephyr.text.editor",flags= Gio.ApplicationFlags.HANDLES_OPEN|Gio.ApplicationFlags.NON_UNIQUE)
elif SINGLE_APP == 0:
    app = MyApp(application_id="com.zephyr.text.editor",flags= Gio.ApplicationFlags.HANDLES_OPEN)
app.run(sys.argv)
