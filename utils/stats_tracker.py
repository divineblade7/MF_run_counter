from init import *
from utils import tk_dynamic as tkd, tk_utils, color_themes
import pymem.exception
import tkinter as tk
import time
import os

#FIXME: Quit if turning off advanced automode
class StatsTracker(tkd.Toplevel):
    def __init__(self, main_frame, **kw):
        tkd.Toplevel.__init__(self, **kw)
        self.main_frame = main_frame

        self.title('Stats tracker')
        self.wm_attributes('-topmost', main_frame.always_on_top)

        disp_coords = tk_utils.get_displaced_geom(main_frame.root, 240, 299)
        self.geometry(disp_coords)
        self.focus_get()
        self.iconbitmap(os.path.join(getattr(sys, '_MEIPASS', os.path.abspath('.')), media_path + 'icon.ico'))
        self.resizable(False, False)

        self.session_char_xp_start = 0
        self.session_char_xp = 0
        self.session_char_xp_diff = 0
        self.session_char_time_start = 0
        self.session_char_xp_missing = 0
        self.xp_hour_session = 0
        self.xp_runs = set()

        self.make_widgets()

        color_themes.Theme(main_frame.active_theme).update_colors()
        self._update_loop()

    def make_widgets(self):
        tkd.Label(self, text='Advanced stats tracker', font='Helvetica 15').pack()
        lf1 = tkd.LabelFrame(self)
        lf1.pack(expand=False, fill=tk.X, padx=1)
        self.name_sv = self.create_row('Name', lf=lf1)
        self.level_sv = self.create_row('Level', lf=lf1)
        self.mf_sv = self.create_row('MF', lf=lf1)
        self.players_x_sv = self.create_row('Players X', lf=lf1)
        lf2 = tkd.LabelFrame(self)
        lf2.pack(expand=False, fill=tk.X, padx=1, pady=8)
        self.exp_sv = self.create_row('Exp %', lf=lf2)
        self.exp_session_sv = self.create_row('Exp (session)', lf=lf2, default_val='0')
        self.exp_run_sv = self.create_row('Exp (run)', lf=lf2, default_val='0')
        self.exp_hour_sv = self.create_row('Exp / hour', lf=lf2, default_val='0')
        lf3 = tkd.LabelFrame(self)
        lf3.pack(expand=False, fill=tk.X, padx=1)
        self.exp_level_sv = self.create_row('Exp to level', lf=lf3)
        self.hours_level_sv = self.create_row('Hours to level', lf=lf3)
        self.runs_level_sv = self.create_row('Runs to level', lf=lf3)

    def create_row(self, var_name, lf, default_val='-----'):
        fr = tkd.Frame(lf, height=22, width=236)
        fr.propagate(False)
        fr.pack(expand=False, fill=tk.X)

        sv = tk.StringVar(fr, value=default_val)
        tkd.Label(fr, text='%s:' % var_name, font='helvetica 10', anchor=tk.W, justify=tk.LEFT).pack(side=tk.LEFT)
        tkd.Label(fr, textvariable=sv, font='helvetica 12 bold', anchor=tk.E, justify=tk.RIGHT).pack(side=tk.RIGHT)

        return sv

    def _update_loop(self):
        self._update_vars()
        self._updater = self.after(600, self._update_loop)

    def _update_vars(self):
        try:
            player_unit_stats = self.main_frame.d2_reader.player_unit_stats()
            players_x = self.main_frame.d2_reader.players_x()
        except (pymem.exception.MemoryReadError, AttributeError, KeyError, pymem.exception.WinAPIError, pymem.exception.ProcessError) as e:
            self.xp_hour_session = 3600 * self.session_char_xp_diff / (time.time() + 0.0001 - self.session_char_time_start)
            self.exp_hour_sv.set('{:,.0f}'.format(self.xp_hour_session))
            self.hours_level_sv.set('{:,.2f}'.format(self.session_char_xp_missing / self.xp_hour_session) if self.xp_hour_session > 0 else '-----')
            if hasattr(self, 'curr_run_xp') and self.session_char_xp != self.curr_run_xp:
                self.xp_runs.add(self.session_char_xp - self.curr_run_xp)
                avg_run = sum(self.xp_runs)/len(self.xp_runs)
                self.runs_level_sv.set('{:.0f}'.format(-(-self.session_char_xp_missing/avg_run//1)))
            self.curr_run_xp = self.session_char_xp
            self.exp_run_sv.set('0')
            return
        if player_unit_stats['Exp'] == -1:
            return

        if not hasattr(self, 'curr_run_xp'):
            self.curr_run_xp = player_unit_stats['Exp']

        new_name = player_unit_stats['Name']
        if new_name != self.name_sv.get():
            self.session_char_xp_start = player_unit_stats['Exp']
            self.session_char_time_start = time.time()
            self.curr_run_xp = self.session_char_xp_start
            self.name_sv.set(new_name)
            self.xp_runs = set()
            self.runs_level_sv.set('-----')
        self.level_sv.set(player_unit_stats['Level'])
        if player_unit_stats['MF'] >= 0:
            self.mf_sv.set(str(player_unit_stats['MF']) + '%')
        self.players_x_sv.set(players_x)

        self.exp_sv.set('{0:.1f}%'.format(player_unit_stats['Exp %']*100))

        self.session_char_xp = player_unit_stats['Exp']
        self.session_char_xp_diff = self.session_char_xp - self.session_char_xp_start
        self.exp_session_sv.set('{:,.0f}'.format(self.session_char_xp_diff))

        self.xp_hour_session = 3600 * self.session_char_xp_diff / (time.time() + 0.0001 - self.session_char_time_start)
        self.exp_hour_sv.set('{:,.0f}'.format(self.xp_hour_session))
        self.exp_run_sv.set('{:,.0f}'.format(self.session_char_xp - self.curr_run_xp))

        self.session_char_xp_missing = player_unit_stats['Exp missing']
        self.exp_level_sv.set('{:,.0f}'.format(self.session_char_xp_missing))
        self.hours_level_sv.set('{:.2f}'.format(self.session_char_xp_missing / self.xp_hour_session) if self.xp_hour_session > 0 else '-----')

