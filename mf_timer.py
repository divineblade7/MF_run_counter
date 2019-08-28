from init import *
import json
import os
import queue
import sys
import time
import traceback
import webbrowser
import win32api
import win32gui
import win32con
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import github_releases
import sound
import tk_utils
from config import Config
from options import Options
from profiles import Profile
exec(blocks[1])


class MFRunTimer(tk.Frame):
    def __init__(self, main_frame, parent=None, **kw):
        tk.Frame.__init__(self, parent, kw)
        self.main_frame = main_frame
        self._start = 0.0
        self._session_start = time.time()
        self.session_time = 0.0
        self._laptime = 0.0
        self.is_running = False
        self.is_paused = False
        self._waiting_for_delay = False
        self.sessionstr = tk.StringVar()
        self.timestr = tk.StringVar()
        self.no_of_laps = tk.StringVar()
        self.min_lap = tk.StringVar()
        self.avg_lap = tk.StringVar()
        self.laps = []
        self._make_widgets()

        exec(blocks[5])

        self._update_session_time()

    def _make_widgets(self):
        flt = tk.Canvas(self)
        flt.pack(fill=tk.X, expand=tk.NO)
        self.c1, self.circ_id = tk_utils.add_circle(flt, 14, 'red')
        self.c1.grid(row=0, column=0, padx=3, pady=3)
        tk.Label(flt, textvariable=self.sessionstr, font=('arial', 10)).grid(row=0, column=1, sticky=tk.N, padx=20)
        self._set_time(self.session_time, for_session=True)

        tk.Label(self, textvariable=self.timestr, font='arial 20').pack(fill=tk.X, expand=tk.NO, pady=4)
        self._set_time(0, for_session=False)

        l2f = tk.Frame(self)
        l2f.pack(pady=2)
        tk.Label(l2f, text='---- Run count:', font=('arial', 12)).pack(side=tk.LEFT)
        tk.Label(l2f, textvariable=self.no_of_laps, font='arial 15', fg='red').pack(side=tk.LEFT)
        tk.Label(l2f, text='----', font=('arial', 12)).pack(side=tk.LEFT)
        self._set_laps(is_running=False)

        tk.Label(self, textvariable=self.min_lap, font=('arial', 11)).pack(fill=tk.X, expand=tk.NO, pady=3, padx=2)
        self._set_fastest()

        tk.Label(self, textvariable=self.avg_lap, font=('arial', 11)).pack(fill=tk.X, expand=tk.NO, pady=3, padx=2)
        self._set_average()

        lf0 = tk.Frame(self)
        lf0.pack()
        scrollbar = tk.Scrollbar(lf0, orient=tk.VERTICAL)
        self.m = tk.Listbox(lf0, selectmode=tk.EXTENDED, height=5, yscrollcommand=scrollbar.set, activestyle='none', font=('courier', 12))
        self.m.bind('<FocusOut>', lambda e: self.m.selection_clear(0, tk.END))
        self.m.bindtags((self.m, self, "all"))
        self.m.pack(side=tk.LEFT, fill=tk.BOTH, expand=1, pady=5)
        scrollbar.config(command=self.m.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _update_lap_time(self):
        self._laptime = time.time() - self._start
        self._set_time(self._laptime, for_session=False)
        self._timer = self.after(50, self._update_lap_time)

    def _update_session_time(self):
        self.session_time = time.time() - self._session_start
        self._set_time(self.session_time, for_session=True)
        self._sess_timer = self.after(50, self._update_session_time)

    exec(blocks[6])

    def _set_time(self, elap, for_session):
        time_str = tk_utils.build_time_str(elap)
        if for_session:
            self.session_time_str = time_str
            self.sessionstr.set('Session time: ' + self.session_time_str)
        else:
            self.timestr.set(time_str)

    def _set_laps(self, is_running):
        run_count = len(self.laps)
        if is_running:
            run_count += 1
        self.no_of_laps.set(run_count)

    def _set_fastest(self):
        if self.laps:
            self.min_lap.set('Fastest time: %s' % tk_utils.build_time_str(min(self.laps)))
        else:
            self.min_lap.set('Fastest time: --:--:--.-')

    def _set_average(self):
        if self.laps:
            self.avg_lap.set('Average time: %s' % tk_utils.build_time_str(sum(self.laps) / len(self.laps)))
        else:
            self.avg_lap.set('Average time: --:--:--.-')

    def load_from_state(self, state):
        self.laps = []
        self.m.delete(0, tk.END)
        self.session_time = state.get('session_time', 0)
        self._session_start = time.time() - self.session_time
        for lap in state.get('laps', []):
            self.Lap(lap, force=True)
        self._set_laps(is_running=False)
        self._set_fastest()
        self._set_average()
        self._set_time(self.session_time, for_session=True)

    def Start(self, play_sound=True):
        def update_start():
            if self.is_paused:
                self.Pause()
            self.c1.itemconfigure(self.circ_id, fill='green3')
            self._start = time.time() - self._laptime
            self._update_lap_time()
            self.is_running = True
            self._set_laps(self.is_running)
            self._waiting_for_delay = False

        if not self.is_running:
            if play_sound and self.main_frame.enable_sound_effects:
                sound.queue_sound(self)
            delay = self.main_frame.run_timer_delay_seconds
            if delay > 0:
                if self._waiting_for_delay:
                    return
                self._waiting_for_delay = True
                self.after(int(delay*1000), update_start)
            else:
                update_start()

    def Stop(self, play_sound=True):
        if self.is_running:
            self.Lap(self._laptime)
            self.c1.itemconfigure(self.circ_id, fill='red')
            self._laptime = 0.0
            self.is_running = False
            self._set_time(0, for_session=False)
            self.after_cancel(self._timer)
            if play_sound and self.main_frame.enable_sound_effects:
                sound.queue_sound(self)

    def StopStart(self):
        self.Stop(play_sound=False)
        self.Start(play_sound=False)
        if self.main_frame.enable_sound_effects:
            sound.queue_sound(self)

    def Lap(self, laptime, force=False):
        if self.is_running or force:
            self.laps.append(laptime)
            str_n = ' ' * max(3 - len(str(len(self.laps))), 0) + str(len(self.laps))
            self.m.insert(tk.END, 'Run ' + str_n + ': ' + tk_utils.build_time_str(self.laps[-1]))
            self.m.yview_moveto(1)
            self._set_laps(is_running=False)
            self._set_fastest()
            self._set_average()

    def DeletePrev(self):
        if self.laps:
            self.m.delete(tk.END)
            self.laps.pop()
            self._set_laps(is_running=self.is_running)
            self._set_fastest()
            self._set_average()

    def Pause(self):
        if not self.is_paused:
            self.pause_lab = tk.Button(self, font='arial 24 bold', text='Resume', bg='deep sky blue', command=self.Pause)
            self.pause_lab.pack()
            self.pause_lab.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

            self.c1.itemconfigure(self.circ_id, fill='red')
            self._set_time(self._laptime, for_session=False)
            self._set_time(self.session_time, for_session=True)
            if self.is_running:
                self.after_cancel(self._timer)
            self.after_cancel(self._sess_timer)
            exec(blocks[7])
            self.is_paused = True
        else:
            self.pause_lab.destroy()
            self._start = time.time() - self._laptime
            self._session_start = time.time() - self.session_time
            if self.is_running:
                self.c1.itemconfigure(self.circ_id, fill='green3')
                self._update_lap_time()
            self._update_session_time()
            exec(blocks[8])
            self.is_paused = False

    def ResetLap(self):
        if self.is_running:
            self._start = time.time()
            self._laptime = 0.0
            self._set_time(self._laptime, for_session=False)

    def ResetSession(self):
        if self.is_running:
            self.Stop()
        self._start = time.time()
        self._laptime = 0.0
        self.session_time = 0.0
        self._session_start = time.time()
        self.laps = []
        self.m.delete(0, tk.END)
        self._set_time(self._laptime, for_session=False)
        self._set_time(self.session_time, for_session=True)
        self._set_laps(is_running=self.is_running)
        self._set_fastest()
        self._set_average()

    def SaveState(self):
        return dict(laps=self.laps, session_time=self.session_time)


class Drops(tk.Frame):
    def __init__(self, tab1, parent=None, **kw):
        tk.Frame.__init__(self, parent, kw)
        self.drops = dict()
        self.tab1 = tab1
        lf = tk.Frame(self)
        lf.pack(expand=1, fill=tk.BOTH)
        scrollbar = tk.Scrollbar(lf, orient=tk.VERTICAL)
        self.m = tk.Listbox(lf, selectmode=tk.EXTENDED, height=5, yscrollcommand=scrollbar.set, activestyle='none', font=('courier', 12))
        self.m.bind('<FocusOut>', lambda e: self.m.selection_clear(0, tk.END))
        self.m.pack(side=tk.LEFT, fill=tk.BOTH, expand=1, pady=5, padx=2)
        scrollbar.config(command=self.m.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        btn = tk.Button(self, text='Delete selection', command=self.delete)
        btn.bind_all('<Delete>', lambda e: self.delete())
        btn.pack(side=tk.BOTTOM)

    def AddDrop(self):
        drop = tk_utils.mbox('Input your drop', entry=True, title='Add drop')
        if not drop:
            return
        run_no = len(self.tab1.laps)
        if self.tab1.is_running:
            run_no += 1
        self.drops.setdefault(str(run_no), []).append(drop)
        self.display_drop(drop=drop, run_no=run_no)

    def display_drop(self, drop, run_no):
        self.m.insert(tk.END, 'Run %s: %s' % (run_no, drop))
        self.m.yview_moveto(1)

    def delete(self):
        selection = self.m.curselection()
        if selection:
            ss = self.m.get(selection[0])
            run_no = ss[4:ss.find(':')]
            drop = ss[ss.find(':')+2:]
            self.drops[run_no].remove(drop)
            self.m.delete(selection[0])

    def save_state(self):
        return self.drops

    def load_from_state(self, state):
        self.m.delete(0, tk.END)
        self.drops = state.get('drops', dict())
        for run in sorted(self.drops.keys(), key=lambda x: int(x)):
            for drop in self.drops[run]:
                self.display_drop(drop=drop, run_no=run)


class About(tk.Frame):
    def __init__(self, parent=None, **kw):
        tk.Frame.__init__(self, parent, kw)
        label0 = tk.Label(self, text="""Run counter for Diablo 2 developed in July 
and August2019 by *oskros on Path of 
Diablo. Please see the README.md file 
available on Github""", justify=tk.LEFT)
        label0.pack()
        link0 = tk.Label(self, text="Open Readme", fg="blue", cursor="hand2")
        link0.pack()
        link0.bind("<Button-1>", lambda e: webbrowser.open_new(release_repo.rstrip('releases') + 'blob/master/README.md'))

        label = tk.Label(self, text="\n\nVisit the page below for new releases")
        label.pack()

        link1 = tk.Label(self, text="Release Hyperlink", fg="blue", cursor="hand2")
        link1.pack()
        link1.bind("<Button-1>", lambda e: webbrowser.open_new(release_repo))

        lab2 = tk.Label(self, text="\n\nCurrent version: %s" % version)
        lab2.pack(side=tk.BOTTOM)


class MainFrame(Config, tk_utils.MovingFrame, tk_utils.TabSwitch):
    def __init__(self):
        # Create root
        self.root = tk.Tk()

        # Configure error handling
        self.root.report_callback_exception = self.report_callback_exception

        # Create hotkey queue and initiate process for monitoring the queue
        self.queue = queue.Queue(maxsize=1)
        self.process_queue()

        # Build/load config file
        self.cfg = self.load_config_file()
        self.always_on_top = eval(self.cfg['OPTIONS']['always_on_top'])
        self.tab_switch_keys_global = eval(self.cfg['OPTIONS']['tab_switch_keys_global'])
        self.check_for_new_version = eval(self.cfg['OPTIONS']['check_for_new_version'])
        self.enable_sound_effects = eval(self.cfg['OPTIONS']['enable_sound_effects'])
        self.run_timer_delay_seconds = eval(self.cfg['DEFAULT']['run_timer_delay_seconds'])

        # Check for version update
        if self.check_for_new_version:
            github_releases.check_newest_version(release_repo)

        # Load profile info
        self.active_profile = self.cfg['DEFAULT']['active_profile']
        self.profiles = {(self.active_profile)}
        active_state = self.load_state_file()
        self.profiles.update({x.rstrip('json').rstrip('.') for x in os.listdir('Profiles')})
        self.profiles = sorted(self.profiles)

        # Modify root window
        self.root.title('MF run counter')
        self.clickthrough = False
        self.root.resizable(False, False)
        self.root.config(borderwidth=3, relief='raised', height=405, width=240)
        self.root.geometry('+%d+%d' % eval(self.cfg['DEFAULT']['window_start_position']))
        self.root.wm_attributes("-topmost", self.always_on_top)
        self.root.focus_get()
        self.root.protocol("WM_DELETE_WINDOW", self.Quit)
        self.root.iconbitmap(os.path.join(getattr(sys, '_MEIPASS', os.path.abspath('.')), media_path + 'icon.ico'))
        self.root.pack_propagate(False)

        # Build banner image and make window draggable on the banner
        d2icon = os.path.join(getattr(sys, '_MEIPASS', os.path.abspath('.')), media_path + 'd2icon.png')
        img = tk.PhotoImage(file=d2icon)
        self.img_panel = tk.Label(self.root, image=img)
        self.img_panel.pack()
        self.img_panel.bind("<ButtonPress-1>", self._start_move)
        self.img_panel.bind("<ButtonRelease-1>", self._stop_move)
        self.img_panel.bind("<B1-Motion>", self._on_motion)

        # Build tabs
        self.tabcontrol = ttk.Notebook(self.root)
        self.tab1 = MFRunTimer(self, parent=self.tabcontrol)
        self.tab2 = Drops(self.tab1, parent=self.tabcontrol)
        self.tab3 = Options(self, self.tab1, self.tab2, parent=self.tabcontrol)
        self.tab4 = Profile(self, parent=self.tabcontrol)
        self.tab5 = About(parent=self.tabcontrol)
        self.tabcontrol.add(self.tab1, text='Timer')
        self.tabcontrol.add(self.tab2, text='Drops')
        self.tabcontrol.add(self.tab3, text='Options')
        self.tabcontrol.add(self.tab4, text='Profile')
        self.tabcontrol.add(self.tab5, text='About')
        self.tabcontrol.pack(expand=1, fill='both')
        self.root.bind("<<NotebookTabChanged>>", lambda e: self.notebook_tab_change())

        # Add buttons to main widget
        lf = tk.LabelFrame(self.root, height=35)
        lf.propagate(False)  # dont allow buttons to modify label frame size
        lf.pack(expand=True, fill=tk.BOTH)
        tk.Button(lf, text='Start\nnew run', command=self.tab1.StopStart).pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        tk.Button(lf, text='End\nthis run', command=self.tab1.Stop).pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        tk.Button(lf, text='Add\ndrop', command=self.tab2.AddDrop).pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        tk.Button(lf, text='Reset\nlap', command=self.tab1.ResetLap).pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        tk.Button(lf, text='Archive\n& reset', command=self.ArchiveReset).pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        # Register binds for changing tabs
        if self.tab_switch_keys_global:
            self.tab3.tab1.hk.register(['control', 'shift', 'next'], callback=lambda event: self._next_tab())
            self.tab3.tab1.hk.register(['control', 'shift', 'prior'], callback=lambda event: self._prev_tab())
        else:
            self.root.bind_all('<Control-Shift-Next>', lambda event: self._next_tab())
            self.root.bind_all('<Control-Shift-Prior>', lambda event: self._prev_tab())

        # Load save state and start autosave process
        self.LoadActiveState(active_state)
        self._autosave_state()

        # Start the program
        self.root.mainloop()

    def process_queue(self):
        """
        The system hotkeys are registered in child threads, and thus tkinter needs a queue to process hotkey calls to
        achieve a threadsafe system
        """
        try:
            self.queue.get(False)()
            self.root.after(50, lambda: self.process_queue())
        except queue.Empty:
            self.root.after(50, lambda: self.process_queue())

    def set_clickthrough(self):
        """
        Allow for making mouse clicks pass through the window, in case you want to use it as an overlay in your game
        Also makes the window transparent to visualize this effect.
        Calling the function again reverts the window to normal state.
        """
        hwnd = win32gui.FindWindow(None, "MF run counter")
        if not self.clickthrough:
            # Get window style and perform a 'bitwise or' operation to make the style layered and transparent, achieving
            # the clickthrough property
            l_ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            l_ex_style |= win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, l_ex_style)

            # Set the window to be transparent and appear always on top
            win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(0, 0, 0), 190, win32con.LWA_ALPHA)  # transparent
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, self.root.winfo_x(), self.root.winfo_y(), 0, 0, 0)
            self.clickthrough = True
        else:
            # Calling the function again sets the extended style of the window to zero, reverting to a standard window
            win32api.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, 0)
            if not self.always_on_top:
                # Remove the always on top property again, in case always on top was set to false in options
                win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, self.root.winfo_x(), self.root.winfo_y(), 0, 0, 0)
            self.clickthrough = False

    def report_callback_exception(self, *args):
        """
        Handles occuring errors in the application, showing a messagebox with the occured error that user can send back
        for bug fixing
        """
        err = traceback.format_exception(*args)
        tk.messagebox.showerror('Exception occured', err)
        self.Quit()

    def notebook_tab_change(self):
        """
        When tab is switched to profile, the run counter is paused and descriptive statistics are updated. Perhaps it
        should also pause when going to the Options tab?
        """
        x = self.tabcontrol.select()
        if x.endswith('profile'):
            if not self.tab1.is_paused:
                self.tab1.Pause()
            self.tab4.update_descriptive_statistics()
        # A 'hack' to ensure that dropdown menus don't take focus immediate when you switch tabs by focusing the banner
        # image instead :)
        self.img_panel.focus_force()

    def load_state_file(self):
        """
        Loads the save file for the active profile. Ensures directory exists, and if not it is created. Ensures the
        file exists, and if not an empty dictionary is returned.
        """
        if not os.path.isdir('Profiles'):
            os.makedirs('Profiles')
        file = 'Profiles/%s.json' % self.active_profile
        if not os.path.isfile(file):
            state = dict()
        else:
            with open(file, 'r') as fo:
                state = json.load(fo)
        return state

    def _autosave_state(self):
        """
        Function to run the autosave loop that saves the profile every 30 seconds
        """
        self.SaveActiveState()
        self.root.after(30000, self._autosave_state)

    def ResetSession(self):
        """
        Resets session for the timer module and drops from the drops module
        """
        self.tab1.ResetSession()
        self.tab2.drops = dict()
        self.tab2.m.delete(0, tk.END)

    def ArchiveReset(self):
        """
        If any laps or drops have been recorded, this function saves the current session to the profile archive, and
        resets all info in the active session. In case no runs/drops are recorded, the session timer is simply reset
        """
        xc = self.root.winfo_rootx() - self.root.winfo_width()//12
        yc = self.root.winfo_rooty() + self.root.winfo_height()//3

        if not self.tab1.laps and not self.tab2.drops:
            self.ResetSession()
            return
        user_confirm = tk_utils.mbox('Would you like to save and reset session?', b1='Yes', b2='No', coords=[xc, yc])
        if user_confirm:
            # Stop any active run and load current session info from timer and drop module.
            self.tab1.Stop()
            active = self.tab1.SaveState()
            active.update(dict(drops=self.tab2.save_state()))

            # Update session dropdown for the profile
            stamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            self.tab4.available_archive.append(stamp)
            self.tab4.archive_dropdown['values'] = self.tab4.available_archive

            # Update profile .json with the session
            state = self.load_state_file()
            state['active_state'] = dict()
            state[stamp] = active
            file = 'Profiles/%s.json' % self.active_profile
            with open(file, 'w') as fo:
                json.dump(state, fo, indent=2)

            # When session has been successfully saved, the session is reset
            self.ResetSession()

    def LoadActiveState(self, state):
        """
        Loads the input state into the timer and drop modules. This is called at start-up when loading the profile .json
        and when you change the active profile in the profiles tab.
        """
        active_state = state.get('active_state', dict())
        self.tab1.load_from_state(active_state)
        self.tab2.load_from_state(active_state)

    def SaveActiveState(self):
        """
        Loads the .json for the profile, and replaces the 'active_state' key with the current active state, whereafter
        it is saved to file.
        """
        cache = self.load_state_file()
        cache['active_state'] = self.tab1.SaveState()
        cache['active_state'].update(dict(drops=self.tab2.save_state()))
        file = 'Profiles/%s.json' % self.active_profile
        with open(file, 'w') as fo:
            json.dump(cache, fo, indent=2)

    def Quit(self):
        """
        Stops the active run, updates config, saves current state to profile .json, and finally calls 'os._exit',
        terminating all active threads.
        """
        if self.tab1.is_running:
            self.tab1.Stop()
        self.update_config(self)
        self.SaveActiveState()
        os._exit(0)


MainFrame()
