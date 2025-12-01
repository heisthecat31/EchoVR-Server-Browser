import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
import json
import threading
import time
from datetime import datetime
import webbrowser
import queue
import sys

class VerticalScrolledFrame(ttk.Frame):
    """A scrollable frame that properly handles background colors"""
    def __init__(self, parent, bg_color='#2c3e50', *args, **kw):
        super().__init__(parent, *args, **kw)
        self.bg_color = bg_color
        
        self.canvas = tk.Canvas(self, 
                               bg=bg_color,
                               highlightthickness=0,
                               bd=0)
        self.vscrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL)
        
        self.vscrollbar.config(command=self.canvas.yview)
        self.canvas.config(yscrollcommand=self.vscrollbar.set)
        
        self.vscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.interior = tk.Frame(self.canvas, bg=bg_color)
        self.interior_id = self.canvas.create_window(0, 0, 
                                                    window=self.interior, 
                                                    anchor=tk.NW,
                                                    tags="interior")
        
        self.interior.bind('<Configure>', self._configure_interior)
        self.canvas.bind('<Configure>', self._configure_canvas)
        self.canvas.bind('<Enter>', self._bind_to_mousewheel)
        self.canvas.bind('<Leave>', self._unbind_from_mousewheel)
        
        import platform
        self.os_type = platform.system()
        
        self.canvas.bind('<Configure>', lambda e: self._configure_canvas(None))
        
    def _configure_interior(self, event):
        """Update scroll region when interior frame changes size"""
        if self.interior.winfo_reqwidth() != self.canvas.winfo_width():
            self.canvas.itemconfigure(self.interior_id, width=self.canvas.winfo_width())
        
        self.canvas.config(scrollregion=(0, 0, 
                                        self.interior.winfo_reqwidth(), 
                                        self.interior.winfo_reqheight()))
    
    def _configure_canvas(self, event):
        """Update canvas when resized"""
        if self.interior.winfo_reqwidth() != self.canvas.winfo_width():
            self.canvas.itemconfigure(self.interior_id, width=self.canvas.winfo_width())
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
    
    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling"""
        if self.os_type == "Linux":
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def _bind_to_mousewheel(self, event):
        """Bind mousewheel events"""
        if self.os_type == "Linux":
            self.canvas.bind_all("<Button-4>", self._on_mousewheel)
            self.canvas.bind_all("<Button-5>", self._on_mousewheel)
        else:
            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
    
    def _unbind_from_mousewheel(self, event):
        """Unbind mousewheel events"""
        if self.os_type == "Linux":
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")
        else:
            self.canvas.unbind_all("<MouseWheel>")

class EchoVRSpectatorGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("EchoVR Spectator - Server Browser")
        self.root.geometry("1400x900")
        
        self.colors = {
            'bg_dark': '#0f1117',        # Dark background
            'bg_medium': '#1a1d29',      # Medium background
            'bg_light': '#242837',       # Light background
            'card_bg': '#2a2f42',        # Card background
            'text_primary': '#e2e8f0',   # Primary text
            'text_secondary': '#94a3b8', # Secondary text
            'text_muted': '#64748b',     # Muted text
            'accent_blue': '#3b82f6',    # Blue accent
            'accent_green': '#10b981',   # Green accent
            'accent_orange': '#f59e0b',  # Orange accent
            'accent_red': '#ef4444',     # Red accent
            'border': '#334155',         # Border color
            'blue_team': '#60a5fa',      # Blue team color
            'orange_team': '#fb923c',    # Orange team color
        }
        
        self.root.configure(bg=self.colors['bg_dark'])
        
        self.echo_api_ip = "127.0.0.1"
        self.echo_api_port = 6721
        self.api_base_url = f"http://{self.echo_api_ip}:{self.echo_api_port}"

        self.servers = []
        self.selected_server = None
        self.current_session = None
        self.last_update = None
        self.running = True
        
        self.create_widgets()
        
        self.start_background_threads()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.center_window()

    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def create_widgets(self):
        """Create all GUI widgets"""
        main_container = tk.Frame(self.root, bg=self.colors['bg_dark'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.create_header(main_container)
        
        self.create_content_area(main_container)
        
        self.create_footer(main_container)

    def create_header(self, parent):
        """Create header section"""
        header_frame = tk.Frame(parent, bg=self.colors['bg_dark'])
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_frame = tk.Frame(header_frame, bg=self.colors['bg_dark'])
        title_frame.pack(side=tk.LEFT)
        
        title_label = tk.Label(title_frame,
                              text="EchoVR Server Browser",
                              font=('Segoe UI', 24, 'bold'),
                              fg=self.colors['text_primary'],
                              bg=self.colors['bg_dark'])
        title_label.pack(anchor=tk.W)
        
        subtitle_label = tk.Label(title_frame,
                                 text="Browse and join Echo Arena/Combat servers",
                                 font=('Segoe UI', 11),
                                 fg=self.colors['text_secondary'],
                                 bg=self.colors['bg_dark'])
        subtitle_label.pack(anchor=tk.W, pady=(2, 0))
        
        controls_frame = tk.Frame(header_frame, bg=self.colors['bg_dark'])
        controls_frame.pack(side=tk.RIGHT)
        
        refresh_btn = tk.Button(controls_frame,
                               text="🔄 Refresh",
                               command=self.refresh_servers,
                               bg=self.colors['accent_blue'],
                               fg='white',
                               font=('Segoe UI', 10, 'bold'),
                               relief='flat',
                               padx=20,
                               pady=8,
                               cursor='hand2')
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        settings_btn = tk.Button(controls_frame,
                                text="⚙️ Settings",
                                command=self.show_settings,
                                bg=self.colors['bg_light'],
                                fg=self.colors['text_primary'],
                                font=('Segoe UI', 10),
                                relief='flat',
                                padx=20,
                                pady=8,
                                cursor='hand2')
        settings_btn.pack(side=tk.LEFT, padx=5)
        
        self.status_indicator = tk.Label(controls_frame,
                                        text="●",
                                        font=('Segoe UI', 14),
                                        fg=self.colors['accent_red'],
                                        bg=self.colors['bg_dark'])
        self.status_indicator.pack(side=tk.LEFT, padx=(15, 5))
        
        self.status_label = tk.Label(controls_frame,
                                    text="Disconnected",
                                    font=('Segoe UI', 10),
                                    fg=self.colors['text_secondary'],
                                    bg=self.colors['bg_dark'])
        self.status_label.pack(side=tk.LEFT)

    def create_content_area(self, parent):
        """Create main content area"""
        content_frame = tk.Frame(parent, bg=self.colors['bg_dark'])
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        left_column = tk.Frame(content_frame, bg=self.colors['bg_dark'])
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
        
        list_header = tk.Frame(left_column, bg=self.colors['bg_dark'])
        list_header.pack(fill=tk.X, pady=(0, 15))
        
        list_title = tk.Label(list_header,
                             text="Available Servers",
                             font=('Segoe UI', 16, 'bold'),
                             fg=self.colors['text_primary'],
                             bg=self.colors['bg_dark'])
        list_title.pack(side=tk.LEFT)
        
        self.server_count_label = tk.Label(list_header,
                                          text="0 servers",
                                          font=('Segoe UI', 11),
                                          fg=self.colors['text_secondary'],
                                          bg=self.colors['bg_dark'])
        self.server_count_label.pack(side=tk.RIGHT)
        
        list_container = tk.Frame(left_column, 
                                 bg=self.colors['bg_light'],
                                 highlightbackground=self.colors['border'],
                                 highlightthickness=1)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        self.server_scroll_frame = VerticalScrolledFrame(list_container, 
                                                        bg_color=self.colors['bg_light'])
        self.server_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        self.server_scroll_frame.interior.update_idletasks()
        
        right_column = tk.Frame(content_frame, bg=self.colors['bg_dark'], width=400)
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH)
        right_column.pack_propagate(False)
        
        details_header = tk.Frame(right_column, bg=self.colors['bg_dark'])
        details_header.pack(fill=tk.X, pady=(0, 15))
        
        details_title = tk.Label(details_header,
                                text="Server Details",
                                font=('Segoe UI', 16, 'bold'),
                                fg=self.colors['text_primary'],
                                bg=self.colors['bg_dark'])
        details_title.pack(anchor=tk.W)
        
        self.details_card = tk.Frame(right_column,
                                    bg=self.colors['card_bg'],
                                    padx=20,
                                    pady=25,
                                    highlightbackground=self.colors['border'],
                                    highlightthickness=1)
        self.details_card.pack(fill=tk.BOTH, expand=True)
        
        empty_label = tk.Label(self.details_card,
                              text="Select a server to view details",
                              font=('Segoe UI', 14),
                              fg=self.colors['text_secondary'],
                              bg=self.colors['card_bg'])
        empty_label.pack(expand=True)

    def create_footer(self, parent):
        """Create footer section"""
        footer_frame = tk.Frame(parent, 
                               bg=self.colors['bg_medium'],
                               height=40)
        footer_frame.pack(fill=tk.X, pady=(20, 0))
        footer_frame.pack_propagate(False)
        
        left_footer = tk.Frame(footer_frame, bg=self.colors['bg_medium'])
        left_footer.pack(side=tk.LEFT, fill=tk.Y, padx=20)
        
        self.update_label = tk.Label(left_footer,
                                    text="Last update: Never",
                                    font=('Segoe UI', 9),
                                    fg=self.colors['text_muted'],
                                    bg=self.colors['bg_medium'])
        self.update_label.pack(side=tk.LEFT)
        
        right_footer = tk.Frame(footer_frame, bg=self.colors['bg_medium'])
        right_footer.pack(side=tk.RIGHT, fill=tk.Y, padx=20)
        
        self.api_status_label = tk.Label(right_footer,
                                        text="API: Disconnected",
                                        font=('Segoe UI', 9),
                                        fg=self.colors['accent_red'],
                                        bg=self.colors['bg_medium'])
        self.api_status_label.pack(side=tk.RIGHT)

    def create_server_card(self, server):
        """Create a server card widget with proper team colors"""
        card_frame = tk.Frame(self.server_scroll_frame.interior,
                             bg=self.colors['card_bg'],
                             padx=15,
                             pady=12)
        card_frame.pack(fill=tk.X, pady=6, padx=10)
        
        card_frame.server_data = server
        card_bg = self.colors['card_bg']
        
        card_frame.bind("<Button-1>", lambda e, s=server: self.select_server(s))
        
        header_frame = tk.Frame(card_frame, bg=card_bg)
        header_frame.pack(fill=tk.X, pady=(0, 8))
        
        mode = server.get('mode', 'unknown').replace('_', ' ').title()
        server_id = server.get('id', 'N/A').split('.')[0].upper()
        
        title_label = tk.Label(header_frame,
                              text=f"{mode} - {server_id}",
                              font=('Segoe UI', 11, 'bold'),
                              fg=self.colors['text_primary'],
                              bg=card_bg,
                              cursor='hand2')
        title_label.pack(side=tk.LEFT)
        title_label.bind("<Button-1>", lambda e, s=server: self.select_server(s))
        
        # Status badge
        is_open = server.get('open', False)
        status_text = "OPEN" if is_open else "LOCKED"
        status_color = self.colors['accent_green'] if is_open else self.colors['accent_red']
        
        status_badge = tk.Label(header_frame,
                              text=status_text,
                              font=('Segoe UI', 8, 'bold'),
                              fg='white',
                              bg=status_color,
                              padx=6,
                              pady=2)
        status_badge.pack(side=tk.RIGHT)
        
        info_frame = tk.Frame(card_frame, bg=card_bg)
        info_frame.pack(fill=tk.X)
        
        players = server.get('players', [])
        player_count = len(players)
        player_label = tk.Label(info_frame,
                              text=f"👥 {player_count} players",
                              font=('Segoe UI', 9),
                              fg=self.colors['text_secondary'],
                              bg=card_bg)
        player_label.pack(side=tk.LEFT)
        
        game_state = server.get('game_state', {})
        if game_state:
            blue_score = game_state.get('blue_score', 0)
            orange_score = game_state.get('orange_score', 0)
            
            score_frame = tk.Frame(info_frame, bg=card_bg)
            score_frame.pack(side=tk.RIGHT)
            
            blue_label = tk.Label(score_frame,
                                text=f" {blue_score}",
                                font=('Segoe UI', 9, 'bold'),
                                fg=self.colors['blue_team'],  # Blue color
                                bg=card_bg)
            blue_label.pack(side=tk.LEFT)
            
            separator = tk.Label(score_frame,
                               text=" - ",
                               font=('Segoe UI', 9),
                               fg=self.colors['text_primary'],
                               bg=card_bg)
            separator.pack(side=tk.LEFT)
            
            orange_label = tk.Label(score_frame,
                                  text=f"{orange_score} ",
                                  font=('Segoe UI', 9, 'bold'),
                                  fg=self.colors['orange_team'],  # Orange color
                                  bg=card_bg)
            orange_label.pack(side=tk.LEFT)
            
            if blue_score > orange_score:
                blue_label.config(font=('Segoe UI', 9, 'bold', 'underline'))
            elif orange_score > blue_score:
                orange_label.config(font=('Segoe UI', 9, 'bold', 'underline'))
        
        quick_btn = tk.Button(card_frame,
                            text="Quick Join →",
                            command=lambda s=server: self.join_server(s),
                            bg=self.colors['accent_blue'],
                            fg='white',
                            font=('Segoe UI', 9),
                            relief='flat',
                            padx=15,
                            pady=4,
                            cursor='hand2',
                            activebackground='#4a90e2',
                            activeforeground='white')
        quick_btn.pack(anchor=tk.E, pady=(8, 0))
        
        for child in card_frame.winfo_children():
            if child != quick_btn:
                child.bind("<Button-1>", lambda e, s=server: self.select_server(s))
                if isinstance(child, tk.Frame):
                    for grandchild in child.winfo_children():
                        if grandchild != quick_btn:
                            grandchild.bind("<Button-1>", lambda e, s=server: self.select_server(s))
        
        def on_enter(e):
            card_frame.config(bg='#2d3348')
            for child in card_frame.winfo_children():
                if isinstance(child, tk.Frame):
                    child.config(bg='#2d3348')
                    for grandchild in child.winfo_children():
                        if isinstance(grandchild, tk.Label) and grandchild != status_badge:
                            try:
                                grandchild.config(bg='#2d3348')
                            except:
                                pass
        
        def on_leave(e):
            card_frame.config(bg=card_bg)
            for child in card_frame.winfo_children():
                if isinstance(child, tk.Frame):
                    child.config(bg=card_bg)
                    for grandchild in child.winfo_children():
                        if isinstance(grandchild, tk.Label) and grandchild != status_badge:
                            try:
                                grandchild.config(bg=card_bg)
                            except:
                                pass
        
        card_frame.bind("<Enter>", on_enter)
        card_frame.bind("<Leave>", on_leave)
        
        self.server_scroll_frame.interior.update_idletasks()
        self.server_scroll_frame.canvas.config(scrollregion=self.server_scroll_frame.canvas.bbox("all"))

    def select_server(self, server):
        """Handle server selection"""
        self.selected_server = server
        self.update_server_details(server)

    def update_server_details(self, server):
        """Update the details panel with server information"""
        for widget in self.details_card.winfo_children():
            widget.destroy()
        
        content = tk.Frame(self.details_card, bg=self.colors['card_bg'])
        content.pack(fill=tk.BOTH, expand=True)
        
        mode = server.get('mode', 'unknown').replace('_', ' ').title()
        server_id = server.get('id', 'N/A').split('.')[0].upper()
        
        title_label = tk.Label(content,
                              text=mode,
                              font=('Segoe UI', 18, 'bold'),
                              fg=self.colors['text_primary'],
                              bg=self.colors['card_bg'])
        title_label.pack(anchor=tk.W, pady=(0, 5))
        
        id_label = tk.Label(content,
                           text=f"ID: {server_id}",
                           font=('Segoe UI', 11),
                           fg=self.colors['text_secondary'],
                           bg=self.colors['card_bg'])
        id_label.pack(anchor=tk.W, pady=(0, 20))
        
        is_open = server.get('open', False)
        status_text = "Open" if is_open else "Locked"
        status_color = self.colors['accent_green'] if is_open else self.colors['accent_red']
        
        status_frame = tk.Frame(content, bg=self.colors['card_bg'])
        status_frame.pack(fill=tk.X, pady=(0, 15))
        
        status_title = tk.Label(status_frame,
                               text="Status:",
                               font=('Segoe UI', 10, 'bold'),
                               fg=self.colors['text_secondary'],
                               bg=self.colors['card_bg'])
        status_title.pack(side=tk.LEFT)
        
        status_value = tk.Label(status_frame,
                               text=status_text,
                               font=('Segoe UI', 10, 'bold'),
                               fg=status_color,
                               bg=self.colors['card_bg'])
        status_value.pack(side=tk.RIGHT)
        
        players = server.get('players', [])
        player_count = len(players)
        
        players_frame = tk.Frame(content, bg=self.colors['card_bg'])
        players_frame.pack(fill=tk.X, pady=(0, 15))
        
        players_title = tk.Label(players_frame,
                                text="Players:",
                                font=('Segoe UI', 10, 'bold'),
                                fg=self.colors['text_secondary'],
                                bg=self.colors['card_bg'])
        players_title.pack(side=tk.LEFT)
        
        players_value = tk.Label(players_frame,
                                text=f"{player_count}/14",
                                font=('Segoe UI', 10, 'bold'),
                                fg=self.colors['text_primary'],
                                bg=self.colors['card_bg'])
        players_value.pack(side=tk.RIGHT)
        
        game_state = server.get('game_state', {})
        if game_state:
            blue_score = game_state.get('blue_score', 0)
            orange_score = game_state.get('orange_score', 0)
            
            score_frame = tk.Frame(content, bg=self.colors['card_bg'])
            score_frame.pack(fill=tk.X, pady=(0, 20))
            
            score_title = tk.Label(score_frame,
                                  text="Score:",
                                  font=('Segoe UI', 10, 'bold'),
                                  fg=self.colors['text_secondary'],
                                  bg=self.colors['card_bg'])
            score_title.pack(side=tk.LEFT)
            
            score_value = tk.Label(score_frame,
                                  text=f"🔵 {blue_score} - {orange_score} 🟠",
                                  font=('Segoe UI', 10, 'bold'),
                                  fg=self.colors['text_primary'],
                                  bg=self.colors['card_bg'])
            score_value.pack(side=tk.RIGHT)
        
        button_frame = tk.Frame(content, bg=self.colors['card_bg'])
        button_frame.pack(fill=tk.X, pady=(0, 25))
        
        join_btn = tk.Button(button_frame,
                           text="🚀 JOIN SERVER",
                           command=lambda s=server: self.join_server(s),
                           bg=self.colors['accent_green'],
                           fg='white',
                           font=('Segoe UI', 12, 'bold'),
                           relief='flat',
                           padx=30,
                           pady=12,
                           cursor='hand2')
        join_btn.pack(fill=tk.X, pady=(0, 10))
        
        spectate_btn = tk.Button(button_frame,
                                text="👁 SPECTATE",
                                command=lambda s=server: self.spectate_server(s),
                                bg=self.colors['accent_blue'],
                                fg='white',
                                font=('Segoe UI', 11),
                                relief='flat',
                                padx=30,
                                pady=10,
                                cursor='hand2')
        spectate_btn.pack(fill=tk.X)
        
        player_header = tk.Frame(content, bg=self.colors['card_bg'])
        player_header.pack(fill=tk.X, pady=(0, 10))
        
        player_title = tk.Label(player_header,
                               text=f"Players ({player_count})",
                               font=('Segoe UI', 12, 'bold'),
                               fg=self.colors['text_primary'],
                               bg=self.colors['card_bg'])
        player_title.pack(side=tk.LEFT)
        
        player_container = tk.Frame(content, bg=self.colors['card_bg'], height=200)
        player_container.pack(fill=tk.BOTH, expand=True)
        
        player_canvas = tk.Canvas(player_container,
                                 bg=self.colors['card_bg'],
                                 highlightthickness=0)
        player_scrollbar = tk.Scrollbar(player_container,
                                       orient=tk.VERTICAL,
                                       command=player_canvas.yview)
        
        player_canvas.configure(yscrollcommand=player_scrollbar.set)
        player_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        player_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        player_inner = tk.Frame(player_canvas, bg=self.colors['card_bg'])
        player_canvas.create_window((0, 0), window=player_inner, anchor=tk.NW)
        
        def configure_scrollregion(event):
            player_canvas.configure(scrollregion=player_canvas.bbox("all"))
        
        player_inner.bind("<Configure>", configure_scrollregion)
        
        if players:
            blue_players = [p for p in players if p.get('team') == 'blue']
            orange_players = [p for p in players if p.get('team') == 'orange']
            no_team = [p for p in players if p.get('team') not in ['blue', 'orange']]
            
            if blue_players:
                blue_header = tk.Label(player_inner,
                                      text="🔵 BLUE TEAM",
                                      font=('Segoe UI', 10, 'bold'),
                                      fg=self.colors['blue_team'],
                                      bg=self.colors['card_bg'])
                blue_header.pack(anchor=tk.W, pady=(0, 5))
                
                for player in blue_players:
                    player_label = tk.Label(player_inner,
                                          text=f"• {player.get('display_name', 'Unknown')}",
                                          font=('Segoe UI', 9),
                                          fg=self.colors['text_primary'],
                                          bg=self.colors['card_bg'])
                    player_label.pack(anchor=tk.W, padx=10)
            
            if orange_players:
                if blue_players:
                    tk.Frame(player_inner, height=10, bg=self.colors['card_bg']).pack()
                
                orange_header = tk.Label(player_inner,
                                        text="🟠 ORANGE TEAM",
                                        font=('Segoe UI', 10, 'bold'),
                                        fg=self.colors['orange_team'],
                                        bg=self.colors['card_bg'])
                orange_header.pack(anchor=tk.W, pady=(0, 5))
                
                for player in orange_players:
                    player_label = tk.Label(player_inner,
                                          text=f"• {player.get('display_name', 'Unknown')}",
                                          font=('Segoe UI', 9),
                                          fg=self.colors['text_primary'],
                                          bg=self.colors['card_bg'])
                    player_label.pack(anchor=tk.W, padx=10)
            
            if no_team:
                if blue_players or orange_players:
                    tk.Frame(player_inner, height=10, bg=self.colors['card_bg']).pack()
                
                no_team_header = tk.Label(player_inner,
                                         text="⚪ NO TEAM",
                                         font=('Segoe UI', 10, 'bold'),
                                         fg=self.colors['text_muted'],
                                         bg=self.colors['card_bg'])
                no_team_header.pack(anchor=tk.W, pady=(0, 5))
                
                for player in no_team:
                    player_label = tk.Label(player_inner,
                                          text=f"• {player.get('display_name', 'Unknown')}",
                                          font=('Segoe UI', 9),
                                          fg=self.colors['text_primary'],
                                          bg=self.colors['card_bg'])
                    player_label.pack(anchor=tk.W, padx=10)
        else:
            empty_label = tk.Label(player_inner,
                                  text="No players in server",
                                  font=('Segoe UI', 10),
                                  fg=self.colors['text_muted'],
                                  bg=self.colors['card_bg'])
            empty_label.pack(pady=20)

    def refresh_servers(self):
        """Manually refresh server list"""
        self.status_label.config(text="Fetching servers...")
        threading.Thread(target=self.fetch_servers, daemon=True).start()

    def fetch_servers(self):
        """Fetch servers from EchoVRCE API"""
        try:
            response = requests.get("https://g.echovrce.com/status/matches", timeout=10)
            if response.status_code == 200:
                data = response.json()
                servers = data.get('labels', [])
                
                print(f"Raw data received. Total labels: {len(servers)}")
                
                filtered_servers = []
                arena_count = 0
                combat_count = 0
                
                for i, server in enumerate(servers):
                    mode = server.get('mode', '')
                    print(f"Server {i}: mode='{mode}', open={server.get('open', False)}, players={len(server.get('players', []))}")
                    
                    if mode in ['echo_arena', 'echo_combat']:
                        filtered_servers.append(server)
                        if mode == 'echo_arena':
                            arena_count += 1
                        else:
                            combat_count += 1
                
                print(f"Filtered servers: {len(filtered_servers)} (Arena: {arena_count}, Combat: {combat_count})")
                
                self.servers = filtered_servers
                self.last_update = datetime.now()
                
                self.root.after(0, self.update_server_display)
                self.root.after(0, self.update_status, True, f"Found {len(filtered_servers)} servers")
                
            else:
                print(f"API Error: {response.status_code}")
                self.root.after(0, self.update_status, False, f"API Error: {response.status_code}")
                
        except Exception as e:
            print(f"Error fetching servers: {str(e)}")
            self.root.after(0, self.update_status, False, f"Error: {str(e)}")

    def update_server_display(self):
        """Update server display in GUI"""
        print(f"Updating server display with {len(self.servers)} servers")
        
        for widget in self.server_scroll_frame.interior.winfo_children():
            widget.destroy()
        
        self.servers.sort(key=lambda x: (not x.get('open', False), -len(x.get('players', []))))
        
        for server in self.servers:
            self.create_server_card(server)
            print(f"Created card for server: {server.get('id', 'N/A')} - Open: {server.get('open', False)}")
        
        self.server_count_label.config(text=f"{len(self.servers)} servers")
        
        if self.last_update:
            time_str = self.last_update.strftime("%H:%M:%S")
            self.update_label.config(text=f"Last update: {time_str}")
            
        if len(self.servers) == 0:
            placeholder = tk.Label(self.server_scroll_frame.interior,
                                 text="No servers found",
                                 font=('Segoe UI', 12),
                                 fg=self.colors['text_muted'],
                                 bg=self.colors['bg_light'],
                                 pady=30)
            placeholder.pack()
            print("No servers found, showing placeholder")
        
        self.server_scroll_frame.interior.update_idletasks()
        self.server_scroll_frame.canvas.config(scrollregion=self.server_scroll_frame.canvas.bbox("all"))
        
        print(f"Server display updated. Server count label should show: {len(self.servers)} servers")

    def join_server(self, server):
        """Join a specific server"""
        threading.Thread(target=self._join_server_thread, args=(server,), daemon=True).start()

    def _join_server_thread(self, server):
        """Thread for joining server"""
        server_id = server.get('id', '').split('.')[0].upper()
        
        if not self.check_api_connection():
            self.root.after(0, messagebox.showerror, 
                          "API Error", 
                          "Cannot connect to EchoVR API. Make sure EchoVR is running.")
            return
        
        join_data = {
            "session_id": server_id,
            "password": ""
        }
        
        try:
            response = requests.post(f"{self.api_base_url}/join_session", 
                                    json=join_data, 
                                    timeout=5)
            
            if response.status_code == 200:
                self.current_session = server
                self.root.after(0, messagebox.showinfo, 
                              "Success", 
                              f"Joining server: {server_id}")
            else:
                self.root.after(0, messagebox.showerror, 
                              "Error", 
                              f"Failed to join server: {response.text}")
                
        except Exception as e:
            self.root.after(0, messagebox.showerror, 
                          "Connection Error", 
                          f"Failed to connect to EchoVR API:\n{str(e)}")

    def spectate_server(self, server):
        """Spectate a specific server"""
        self.join_server(server)
        self.root.after(0, messagebox.showinfo, 
                      "Spectator Mode", 
                      "Joining as spectator. Use in-game controls to adjust camera.")

    def check_api_connection(self):
        """Check if EchoVR API is reachable"""
        try:
            response = requests.get(f"{self.api_base_url}/session", timeout=2)
            if response.status_code == 200:
                self.root.after(0, self.update_api_status, True)
                return True
        except:
            pass
        
        self.root.after(0, self.update_api_status, False)
        return False

    def update_api_status(self, connected):
        """Update API status display"""
        if connected:
            self.api_status_label.config(text="API: Connected", fg=self.colors['accent_green'])
            self.status_indicator.config(text="●", fg=self.colors['accent_green'])
            self.status_label.config(text="Connected")
        else:
            self.api_status_label.config(text="API: Disconnected", fg=self.colors['accent_red'])
            self.status_indicator.config(text="●", fg=self.colors['accent_red'])
            self.status_label.config(text="Disconnected")

    def update_status(self, success, message):
        """Update status message"""
        if success:
            self.status_indicator.config(text="●", fg=self.colors['accent_green'])
            self.status_label.config(text=message)
        else:
            self.status_indicator.config(text="●", fg=self.colors['accent_red'])
            self.status_label.config(text=message)

    def show_settings(self):
        """Show settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x300")
        settings_window.configure(bg=self.colors['bg_dark'])
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        settings_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - settings_window.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - settings_window.winfo_height()) // 2
        settings_window.geometry(f"+{x}+{y}")
        
        title = tk.Label(settings_window,
                        text="Settings",
                        font=('Segoe UI', 16, 'bold'),
                        fg=self.colors['text_primary'],
                        bg=self.colors['bg_dark'])
        title.pack(pady=20)
        
        settings_frame = tk.Frame(settings_window, bg=self.colors['bg_medium'], padx=20, pady=20)
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        ip_frame = tk.Frame(settings_frame, bg=self.colors['bg_medium'])
        ip_frame.pack(fill=tk.X, pady=10)
        
        ip_label = tk.Label(ip_frame,
                           text="API IP Address:",
                           font=('Segoe UI', 10),
                           fg=self.colors['text_primary'],
                           bg=self.colors['bg_medium'])
        ip_label.pack(anchor=tk.W, pady=(0, 5))
        
        ip_entry = tk.Entry(ip_frame,
                           font=('Segoe UI', 10),
                           bg=self.colors['card_bg'],
                           fg=self.colors['text_primary'],
                           insertbackground=self.colors['text_primary'])
        ip_entry.pack(fill=tk.X)
        ip_entry.insert(0, self.echo_api_ip)
        
        port_frame = tk.Frame(settings_frame, bg=self.colors['bg_medium'])
        port_frame.pack(fill=tk.X, pady=10)
        
        port_label = tk.Label(port_frame,
                            text="API Port:",
                            font=('Segoe UI', 10),
                            fg=self.colors['text_primary'],
                            bg=self.colors['bg_medium'])
        port_label.pack(anchor=tk.W, pady=(0, 5))
        
        port_entry = tk.Entry(port_frame,
                            font=('Segoe UI', 10),
                            bg=self.colors['card_bg'],
                            fg=self.colors['text_primary'],
                            insertbackground=self.colors['text_primary'])
        port_entry.pack(fill=tk.X)
        port_entry.insert(0, str(self.echo_api_port))
        
        test_btn = tk.Button(settings_window,
                           text="Test Connection",
                           command=lambda: self.test_connection(ip_entry.get(), port_entry.get()),
                           bg=self.colors['accent_blue'],
                           fg='white',
                           font=('Segoe UI', 10),
                           padx=20,
                           pady=8)
        test_btn.pack(pady=10)
        
        save_btn = tk.Button(settings_window,
                           text="Save Settings",
                           command=lambda: self.save_settings(ip_entry.get(), port_entry.get(), settings_window),
                           bg=self.colors['accent_green'],
                           fg='white',
                           font=('Segoe UI', 10, 'bold'),
                           padx=20,
                           pady=10)
        save_btn.pack(pady=10)

    def test_connection(self, ip, port):
        """Test API connection"""
        try:
            response = requests.get(f"http://{ip}:{port}/session", timeout=2)
            if response.status_code == 200:
                messagebox.showinfo("Success", "Connection successful!")
            else:
                messagebox.showerror("Error", f"API responded with status: {response.status_code}")
        except Exception as e:
            messagebox.showerror("Error", f"Connection failed: {str(e)}")

    def save_settings(self, ip, port, window):
        """Save API settings"""
        try:
            self.echo_api_ip = ip
            self.echo_api_port = int(port)
            self.api_base_url = f"http://{self.echo_api_ip}:{self.echo_api_port}"
            window.destroy()
            messagebox.showinfo("Success", "Settings saved successfully!")
        except ValueError:
            messagebox.showerror("Error", "Port must be a valid number!")

    def start_background_threads(self):
        """Start background update threads"""
        def periodic_fetch():
            while self.running:
                self.fetch_servers()
                time.sleep(30)
        
        def periodic_api_check():
            while self.running:
                self.check_api_connection()
                time.sleep(10)
        
        threading.Thread(target=periodic_fetch, daemon=True).start()
        threading.Thread(target=periodic_api_check, daemon=True).start()
        
        self.fetch_servers()
        self.check_api_connection()

    def on_closing(self):
        """Handle window closing"""
        self.running = False
        self.root.destroy()

    def run(self):
        """Start the application"""
        self.root.mainloop()

def main():
    """Main entry point"""
    app = EchoVRSpectatorGUI()
    app.run()

if __name__ == "__main__":
    main()