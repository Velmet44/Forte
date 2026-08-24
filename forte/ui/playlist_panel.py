from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import (
    Qt,
    pyqtSignal,
    QAbstractListModel,
    QModelIndex,
    QSize,
    QRect,
    QMimeData,
    QUrl,
    QSortFilterProxyModel,
)
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QPainter, QDesktopServices, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QListView,
    QAbstractItemView,
    QToolButton,
    QFileDialog,
    QMenu,
    QStyledItemDelegate,
    QStyle,
)

from forte.metadata import TrackMetadata
from forte.playlist import Playlist

_AUDIO_EXTENSIONS = {".mp3", ".flac", ".wav", ".ogg", ".m4a"}
_MIME = "application/x-forte-track"

TITLE = Qt.ItemDataRole.UserRole + 1
ARTIST = Qt.ItemDataRole.UserRole + 2
DURATION_STR = Qt.ItemDataRole.UserRole + 3
ORIGINAL_INDEX = Qt.ItemDataRole.UserRole + 4
IS_PLAYING = Qt.ItemDataRole.UserRole + 5
FILEPATH = Qt.ItemDataRole.UserRole + 6


class PlaylistModel(QAbstractListModel):
    """List model that wraps a forte.playlist.Playlist object."""

    def __init__(self, playlist: Playlist, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._playlist = playlist
        self._current = -1

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._playlist)

    def data(self, index: QModelIndex, role: int):
        if not index.isValid():
            return None
        row = index.row()
        if row < 0 or row >= len(self._playlist):
            return None
        track = self._playlist[row]
        if role == Qt.ItemDataRole.DisplayRole:
            return track.title
        if role == TITLE:
            return track.title
        if role == ARTIST:
            return track.artist
        if role == DURATION_STR:
            return track.duration_str
        if role == ORIGINAL_INDEX:
            return row
        if role == IS_PLAYING:
            return row == self._current
        if role == FILEPATH:
            return track.filepath
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        default = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if not index.isValid():
            return default | Qt.ItemFlag.ItemIsDropEnabled
        return default | Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsDropEnabled

    def set_current(self, index: int) -> None:
        if index == self._current:
            return
        old, self._current = self._current, index
        for row in {old, index}:
            if 0 <= row < len(self._playlist):
                self.dataChanged.emit(self.index(row, 0), self.index(row, 0))

    def refresh(self) -> None:
        self.beginResetModel()
        self.endResetModel()

    def supportedDropActions(self) -> Qt.DropAction:
        return Qt.DropAction.MoveAction

    def mimeTypes(self) -> list[str]:
        return [_MIME]

    def mimeData(self, indexes: list[QModelIndex]) -> QMimeData:
        data = QMimeData()
        rows = ",".join(str(i.row()) for i in indexes if i.isValid())
        data.setData(_MIME, rows.encode("utf-8"))
        return data

    def dropMimeData(
        self,
        data: QMimeData,
        action: Qt.DropAction,
        row: int,
        column: int,
        parent: QModelIndex,
    ) -> bool:
        if not data.hasFormat(_MIME):
            return False
        text = bytes(data.data(_MIME)).decode("utf-8")
        src_rows = [int(x) for x in text.split(",") if x != ""]
        if not src_rows:
            return False

        n = len(self._playlist)
        if row == -1 and not parent.isValid():
            target = n
        else:
            target = parent.row() if parent.isValid() else row

        remaining = [i for i in range(n) if i not in src_rows]
        before = sum(1 for i in src_rows if i < target)
        insert_at = target - before
        if insert_at < 0:
            insert_at = 0
        if insert_at > len(remaining):
            insert_at = len(remaining)

        new_order = remaining[:insert_at] + src_rows + remaining[insert_at:]
        try:
            self._playlist.reorder(new_order)
        except ValueError:
            return False
        self.refresh()
        return True


class PlaylistProxyModel(QSortFilterProxyModel):
    """Filters the playlist by title OR artist, case-insensitively."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        source = self.sourceModel()
        if source is None:
            return True
        text = self.filterRegularExpression().pattern().strip().lower()
        if not text:
            return True
        idx = source.index(source_row, 0)
        title = (source.data(idx, TITLE) or "").lower()
        artist = (source.data(idx, ARTIST) or "").lower()
        return text in f"{title} {artist}"


class TrackDelegate(QStyledItemDelegate):
    """Paints each playlist row with number/▶, title and right-aligned duration."""

    ROW_HEIGHT = 48

    def __init__(self, theme: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.theme = theme

    def sizeHint(self, option, index: QModelIndex) -> QSize:
        width = option.rect.width() if option.rect.width() > 0 else 260
        return QSize(width, self.ROW_HEIGHT)

    def paint(self, painter: QPainter, option, index: QModelIndex) -> None:
        painter.save()
        rect = option.rect
        state = option.state
        is_selected = bool(state & QStyle.StateFlag.State_Selected)
        is_hovered = bool(state & QStyle.StateFlag.State_MouseOver)
        is_playing = bool(index.data(IS_PLAYING))

        bg = self.theme["bg_base"]
        if is_selected or is_hovered:
            bg = self.theme["bg_elevated"]
        painter.fillRect(rect, QColor(bg))

        if is_playing:
            painter.fillRect(QRect(rect.x(), rect.y(), 3, rect.height()), QColor(self.theme["accent"]))

        text_color = QColor(self.theme["text_primary"] if is_playing else self.theme["text_secondary"])
        painter.setPen(text_color)

        left = "▶" if is_playing else str((index.data(ORIGINAL_INDEX) or 0) + 1)
        painter.setFont(QFont("Inter", 10))
        painter.drawText(
            QRect(rect.x() + 8, rect.y(), 24, rect.height()),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            left,
        )

        title = index.data(TITLE) or ""
        title_font = QFont("Inter", 11)
        fm = QFontMetrics(title_font)
        title_rect = QRect(rect.x() + 40, rect.y(), rect.width() - 40 - 56, rect.height())
        elided = fm.elidedText(title, Qt.TextElideMode.ElideRight, title_rect.width())
        painter.setFont(title_font)
        painter.drawText(
            title_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            elided,
        )

        duration = index.data(DURATION_STR) or ""
        painter.setFont(QFont("monospace", 10))
        painter.drawText(
            QRect(rect.x() + rect.width() - 52, rect.y(), 48, rect.height()),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            duration,
        )

        painter.restore()


class PlaylistView(QListView):
    """QListView subclass handling drag-and-drop and delete-key removal."""

    files_dropped = pyqtSignal(list)
    deleteRequested = pyqtSignal(int)

    def __init__(self, theme: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setUniformItemSizes(True)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
            if paths:
                self.files_dropped.emit(paths)
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            super().dropEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Delete and self.currentIndex().isValid():
            source = self.model().mapToSource(self.currentIndex())
            self.deleteRequested.emit(source.row())
            return
        super().keyPressEvent(event)


class PlaylistPanel(QWidget):
    """Left panel: search bar, track list (custom delegate) and a toolbar."""

    track_selected = pyqtSignal(int)
    playlist_changed = pyqtSignal()
    play_next = pyqtSignal(int)

    def __init__(self, playlist: Playlist, theme: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.playlist = playlist
        self.theme = theme
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search tracks…")
        self.search.setFixedHeight(28)
        self.search.textChanged.connect(self._on_search)

        self.model = PlaylistModel(self.playlist)
        self.proxy = PlaylistProxyModel()
        self.proxy.setSourceModel(self.model)

        self.view = PlaylistView(self.theme)
        self.view.setModel(self.proxy)
        self.delegate = TrackDelegate(self.theme)
        self.view.setItemDelegate(self.delegate)
        self.view.doubleClicked.connect(self._on_double_click)
        self.view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self._on_context_menu)
        self.view.files_dropped.connect(self.add_files)
        self.view.deleteRequested.connect(self.remove_track)

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(6, 4, 6, 4)
        toolbar.setSpacing(6)
        toolbar.addWidget(self._tool_button("+", "Add Files", self._add_files))
        toolbar.addWidget(self._tool_button("📁", "Add Folder", self._add_folder))
        toolbar.addWidget(self._tool_button("🗑", "Clear Playlist", self._clear))
        toolbar.addStretch(1)
        toolbar_widget = QWidget()
        toolbar_widget.setLayout(toolbar)
        toolbar_widget.setFixedHeight(32)

        layout.addWidget(self.search)
        layout.addWidget(self.view, 1)
        layout.addWidget(toolbar_widget)

        shortcut = QShortcut(QKeySequence.StandardKey.Find, self)
        shortcut.activated.connect(self.search.setFocus)

    def _tool_button(self, glyph: str, tooltip: str, slot) -> QToolButton:
        btn = QToolButton()
        btn.setText(glyph)
        btn.setToolTip(tooltip)
        btn.setFixedSize(26, 26)
        btn.clicked.connect(slot)
        return btn

    def set_current_track(self, index: int) -> None:
        self.model.set_current(index)

    def _on_search(self, text: str) -> None:
        self.proxy.setFilterFixedString(text)

    def _on_double_click(self, proxy_index: QModelIndex) -> None:
        source = self.proxy.mapToSource(proxy_index)
        if source.isValid():
            self.track_selected.emit(source.row())

    def _on_context_menu(self, point) -> None:
        proxy_index = self.view.indexAt(point)
        if not proxy_index.isValid():
            return
        source = self.proxy.mapToSource(proxy_index)
        index = source.row()

        menu = QMenu(self)
        act_play_next = menu.addAction("Play Next")
        act_remove = menu.addAction("Remove")
        menu.addSeparator()
        act_explorer = menu.addAction("Show in Explorer")

        choice = menu.exec(self.view.viewport().mapToGlobal(point))
        if choice == act_play_next:
            self.play_next.emit(index)
        elif choice == act_remove:
            self.remove_track(index)
        elif choice == act_explorer:
            self._show_in_explorer(index)

    def _show_in_explorer(self, index: int) -> None:
        if not 0 <= index < len(self.playlist):
            return
        path = Path(self.playlist[index].filepath)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.parent)))

    def add_files(self, paths: list[str]) -> None:
        added = False
        for p in paths:
            if Path(p).suffix.lower() in _AUDIO_EXTENSIONS:
                try:
                    self.playlist.add_track(p)
                    added = True
                except Exception:
                    continue
        if added:
            self.model.refresh()
            self.playlist_changed.emit()

    def _add_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Add Files",
            "",
            "Audio Files (*.mp3 *.flac *.wav *.ogg *.m4a)",
        )
        if files:
            self.add_files(files)

    def _add_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Add Folder")
        if folder:
            try:
                added = self.playlist.add_folder(folder)
            except Exception:
                return
            if added:
                self.model.refresh()
                self.playlist_changed.emit()

    def _clear(self) -> None:
        self.playlist.clear()
        self.model.refresh()
        self.playlist_changed.emit()

    def remove_track(self, index: int) -> None:
        if not 0 <= index < len(self.playlist):
            return
        self.playlist.remove_track(index)
        self.model.refresh()
        self.playlist_changed.emit()

    def remove_selected(self) -> None:
        index = self.view.currentIndex()
        if not index.isValid():
            return
        source = self.proxy.mapToSource(index)
        self.remove_track(source.row())

    def selected_source_row(self) -> int | None:
        index = self.view.currentIndex()
        if not index.isValid():
            return None
        return self.proxy.mapToSource(index).row()
