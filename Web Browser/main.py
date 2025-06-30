from PyQt5.QtWidgets import (
    QApplication, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QWidget,
    QSizePolicy, QMenu, QAction, QMainWindow, QTabWidget, QProgressBar,
    QListWidget, QLabel, QFileDialog, QListWidgetItem, QStyle, QStyledItemDelegate,
    QScrollArea, QFrame
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineDownloadItem
from PyQt5.QtCore import QUrl, Qt, QTimer
import sys
import os


class DownloadItemWidget(QWidget):
    def __init__(self, download):
        super().__init__()
        self.download = download

        self.setFixedHeight(60)
        self.setStyleSheet("""
            QWidget {
                border: 1px solid #ccc;
                border-radius: 8px;
                padding: 4px 8px;
                background-color: #f5f5f5;
            }
        """)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(6, 4, 6, 4)
        self.layout.setSpacing(4)

        self.label = QLabel(os.path.basename(download.path()))
        self.label.setStyleSheet("font-size: 12px; font-weight: bold;")
        self.progress = QProgressBar()
        self.progress.setMaximum(100)
        self.progress.setFixedHeight(10)
        self.progress.setTextVisible(False)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.progress)
        self.setLayout(self.layout)

        self.download.finished.connect(self.mark_finished)
        self.download.downloadProgress.connect(self.update_progress)

    def update_progress(self, received, total):
        if total > 0:
            percent = int((received / total) * 100)
            self.progress.setValue(percent)

    def mark_finished(self):
        self.progress.setValue(100)
        self.label.setText(f"{self.label.text()} (Completed)")


class WebBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PaperBrowser")
        self.setGeometry(100, 100, 1200, 800)

        self.history_list = []
        self.bookmarks = []

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)
        self.create_new_tab(QUrl("http://www.google.com"), "New Tab")
        self.tabs.setCornerWidget(self.create_new_tab_button())

        self.download_tab = QWidget()
        self.download_scroll = QScrollArea()
        self.download_scroll.setWidgetResizable(True)
        self.download_container = QWidget()
        self.download_list_layout = QVBoxLayout()
        self.download_list_layout.setAlignment(Qt.AlignTop)
        self.download_container.setLayout(self.download_list_layout)
        self.download_scroll.setWidget(self.download_container)
        dl_layout = QVBoxLayout()
        dl_layout.addWidget(self.download_scroll)
        self.download_tab.setLayout(dl_layout)

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter URL and press Enter")
        self.url_bar.setMinimumWidth(400)
        self.url_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.url_bar.returnPressed.connect(self.load_url)

        back_btn = QPushButton("◀")
        forward_btn = QPushButton("▶")
        refresh_btn = QPushButton("🔄")
        bookmark_btn = QPushButton("Bookmark")
        menu_btn = QPushButton("☰")

        button_style = """
            QPushButton {
                padding: 6px 10px;
                font-size: 14px;
                border: 1px solid #ccc;
                border-radius: 12px;
                background-color: #f9f9f9;
            }
            QPushButton:hover { background-color: #e0e0e0; }
            QPushButton:pressed { background-color: #d0d0d0; }
        """
        for btn in [back_btn, forward_btn, refresh_btn, menu_btn, bookmark_btn]:
            btn.setStyleSheet(button_style)

        back_btn.clicked.connect(lambda: self.current_browser().back())
        forward_btn.clicked.connect(lambda: self.current_browser().forward())
        refresh_btn.clicked.connect(lambda: self.current_browser().reload())
        bookmark_btn.clicked.connect(self.add_bookmark)

        menu = QMenu()
        history_action = QAction("History", self)
        bookmarks_action = QAction("Bookmarks", self)
        download_action = QAction("Downloads", self)

        history_action.triggered.connect(self.show_history)
        bookmarks_action.triggered.connect(self.show_bookmarks)
        download_action.triggered.connect(self.open_download_tab)

        menu.addAction(history_action)
        menu.addAction(bookmarks_action)
        menu.addAction(download_action)

        menu_btn.setMenu(menu)

        nav_layout = QHBoxLayout()
        nav_layout.addWidget(back_btn)
        nav_layout.addWidget(forward_btn)
        nav_layout.addWidget(refresh_btn)
        nav_layout.addWidget(self.url_bar)
        nav_layout.addWidget(bookmark_btn)
        nav_layout.addWidget(menu_btn)

        nav_bar_widget = QWidget()
        nav_bar_widget.setLayout(nav_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(5)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: none; background-color: #eee; }
            QProgressBar::chunk { background-color: #4caf50; }
        """)

        main_layout = QVBoxLayout()
        main_layout.addWidget(nav_bar_widget)
        main_layout.insertWidget(1, self.progress_bar)
        main_layout.addWidget(self.tabs)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def current_browser(self):
        widget = self.tabs.currentWidget()
        return widget if isinstance(widget, QWebEngineView) else None

    def update_url_bar(self, q):
        url = q.toString()
        self.url_bar.setText(url)
        if url not in self.history_list:
            self.history_list.append(url)

    def load_url(self):
        text = self.url_bar.text().strip()
        if not text.startswith("http") and "." not in text:
            url = f"https://www.google.com/search?q={'+'.join(text.split())}"
        elif not text.startswith("http"):
            url = "http://" + text
        else:
            url = text
        browser = self.current_browser()
        if browser:
            browser.setUrl(QUrl(url))

    def create_new_tab(self, url=None, title="New Tab"):
        browser = QWebEngineView()
        browser.setUrl(url or QUrl("http://www.google.com"))

        index = self.tabs.addTab(browser, title)
        self.tabs.setCurrentIndex(index)

        browser.urlChanged.connect(self.update_url_bar)
        browser.titleChanged.connect(lambda t: self.tabs.setTabText(index, t))
        browser.loadStarted.connect(self.on_load_started)
        browser.loadProgress.connect(self.on_load_progress)
        browser.loadFinished.connect(self.on_load_finished)
        browser.page().profile().downloadRequested.connect(self.handle_download)

    def create_new_tab_button(self):
        btn = QPushButton("+")
        btn.setToolTip("New Tab")
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn.setStyleSheet("""
            QPushButton {
                padding: 6px 10px;
                font-size: 14px;
                border: 1px solid #ccc;
                border-radius: 12px;
                background-color: #f9f9f9;
            }
            QPushButton:hover { background-color: #e0e0e0; }
            QPushButton:pressed { background-color: #d0d0d0; }
        """)
        btn.clicked.connect(self.create_new_tab)
        return btn

    def close_tab(self, index):
        if self.tabs.widget(index) == self.download_tab:
            return  # Prevent download tab from being closed
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)
        else:
            browser = self.current_browser()
            if browser:
                browser.setUrl(QUrl("about:blank"))

    def on_load_started(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

    def on_load_progress(self, value):
        self.progress_bar.setValue(value)

    def on_load_finished(self):
        self.progress_bar.setVisible(False)

    def show_history(self):
        self.show_list_dialog("Browsing History", self.history_list, self.load_url_from_list)

    def show_bookmarks(self):
        self.show_list_dialog("Bookmarks", self.bookmarks, self.load_url_from_list)

    def show_list_dialog(self, title, items, callback):
        from PyQt5.QtWidgets import QDialog
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(500, 400)

        layout = QVBoxLayout()
        label = QLabel(title)
        list_widget = QListWidget()
        list_widget.addItems(items)
        list_widget.itemDoubleClicked.connect(lambda item: callback(item.text(), dialog))

        layout.addWidget(label)
        layout.addWidget(list_widget)
        dialog.setLayout(layout)
        dialog.exec_()

    def load_url_from_list(self, url, dialog):
        self.url_bar.setText(url)
        self.load_url()
        dialog.accept()

    def add_bookmark(self):
        url = self.url_bar.text()
        if url and url not in self.bookmarks:
            self.bookmarks.append(url)

    def handle_download(self, download: QWebEngineDownloadItem):
        suggested_path, _ = QFileDialog.getSaveFileName(self, "Save File", download.path())
        if suggested_path:
            download.setPath(suggested_path)
            self.add_download_item(download)
            download.accept()

    def add_download_item(self, download):
        if self.download_tab not in [self.tabs.widget(i) for i in range(self.tabs.count())]:
            self.tabs.addTab(self.download_tab, "Downloads")
        widget = DownloadItemWidget(download)
        self.download_list_layout.addWidget(widget)

    def open_download_tab(self):
        index = self.tabs.indexOf(self.download_tab)
        if index != -1:
            self.tabs.setCurrentIndex(index)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WebBrowser()
    window.show()
    sys.exit(app.exec_())
