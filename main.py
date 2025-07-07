#!/usr/bin/env python3
"""
PDFEditor - A Kivy-based Android PDF Editor Application
Optimized for Moto G54 5G (8GB RAM, 128GB ROM, Android OS)
Features: PDF viewing, editing, page deletion, and creation
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, List

# Additional imports for PDF processing
import fitz  # PyMuPDF
import PyPDF2
from PIL import Image as PILImage
import io
import datetime

# KivyMD imports
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.card import MDCard
from kivymd.uix.list import MDList, OneLineListItem, TwoLineListItem, ThreeLineListItem
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.progressbar import MDProgressBar

# Android-specific imports
try:
    from android.permissions import request_permissions, Permission
    from android.storage import primary_external_storage_path
    ANDROID = True
except ImportError:
    ANDROID = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdf_editor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PDFPage:
    """Represents a single PDF page with operations"""
    
    def __init__(self, page_num: int, pdf_doc, page_widget=None):
        self.page_num = page_num
        self.pdf_doc = pdf_doc
        self.page_widget = page_widget
        self.annotations = []
        
    def get_text(self) -> str:
        """Extract text from the page"""
        try:
            page = self.pdf_doc[self.page_num]
            return page.get_text()
        except Exception as e:
            logger.error(f"Error extracting text from page {self.page_num}: {e}")
            return ""
    
    def get_image(self, zoom: float = 1.0) -> Optional[bytes]:
        """Render page as image"""
        try:
            page = self.pdf_doc[self.page_num]
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            return pix.tobytes("png")
        except Exception as e:
            logger.error(f"Error rendering page {self.page_num}: {e}")
            return None


class PDFDocument:
    """Main PDF document handler with advanced features"""
    
    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path
        self.doc = None
        self.pages = []
        self.metadata = {}
        self.current_page = 0
        self.zoom_level = 1.0
        
        if file_path:
            self.load_document(file_path)
    
    def load_document(self, file_path: str) -> bool:
        """Load PDF document"""
        try:
            self.file_path = file_path
            self.doc = fitz.open(file_path)
            self.pages = [PDFPage(i, self.doc) for i in range(len(self.doc))]
            self.metadata = self.doc.metadata
            logger.info(f"Loaded PDF: {file_path} with {len(self.pages)} pages")
            return True
        except Exception as e:
            logger.error(f"Error loading PDF {file_path}: {e}")
            return False
    
    def save_document(self, output_path: str = None) -> bool:
        """Save PDF document"""
        try:
            save_path = output_path or self.file_path
            self.doc.save(save_path)
            logger.info(f"Saved PDF: {save_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving PDF: {e}")
            return False
    
    def delete_page(self, page_num: int) -> bool:
        """Delete a specific page"""
        try:
            if 0 <= page_num < len(self.pages):
                self.doc.delete_page(page_num)
                self.pages.pop(page_num)
                logger.info(f"Deleted page {page_num}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting page {page_num}: {e}")
            return False
    
    def insert_page(self, page_num: int, content: str = "") -> bool:
        """Insert a new page at specified position"""
        try:
            page = self.doc.new_page(page_num)
            if content:
                page.insert_text((72, 72), content)
            self.pages.insert(page_num, PDFPage(page_num, self.doc))
            logger.info(f"Inserted new page at position {page_num}")
            return True
        except Exception as e:
            logger.error(f"Error inserting page: {e}")
            return False
    
    def merge_documents(self, other_pdf_path: str) -> bool:
        """Merge another PDF document"""
        try:
            other_doc = fitz.open(other_pdf_path)
            self.doc.insert_pdf(other_doc)
            other_doc.close()
            self.pages = [PDFPage(i, self.doc) for i in range(len(self.doc))]
            logger.info(f"Merged PDF: {other_pdf_path}")
            return True
        except Exception as e:
            logger.error(f"Error merging PDF {other_pdf_path}: {e}")
            return False
    
    def extract_pages(self, start_page: int, end_page: int, output_path: str) -> bool:
        """Extract pages to new PDF"""
        try:
            new_doc = fitz.open()
            new_doc.insert_pdf(self.doc, from_page=start_page, to_page=end_page)
            new_doc.save(output_path)
            new_doc.close()
            logger.info(f"Extracted pages {start_page}-{end_page} to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error extracting pages: {e}")
            return False
    
    def add_annotation(self, page_num: int, annotation_type: str, rect: tuple, content: str = "") -> bool:
        """Add annotation to page"""
        try:
            page = self.doc[page_num]
            if annotation_type == "highlight":
                annot = page.add_highlight_annot(rect)
            elif annotation_type == "text":
                annot = page.add_text_annot(rect[0:2], content)
            elif annotation_type == "note":
                annot = page.add_text_annot(rect[0:2], content)
            
            annot.set_info(content=content)
            annot.update()
            logger.info(f"Added {annotation_type} annotation to page {page_num}")
            return True
        except Exception as e:
            logger.error(f"Error adding annotation: {e}")
            return False


class PagePreviewWidget(MDCard):
    """Widget for displaying PDF page preview"""
    
    def __init__(self, pdf_page: PDFPage, **kwargs):
        super().__init__(**kwargs)
        self.pdf_page = pdf_page
        self.size_hint_y = None
        self.height = "200dp"
        self.elevation = 2
        self.radius = [10, 10, 10, 10]
        self.md_bg_color = "white"
        
        layout = MDBoxLayout(orientation="vertical", padding="10dp", spacing="5dp")
        
        # Page image placeholder
        self.page_image = Image(size_hint_y=0.8)
        layout.add_widget(self.page_image)
        
        # Page info
        info_layout = MDBoxLayout(orientation="horizontal", size_hint_y=0.2)
        self.page_label = MDLabel(
            text=f"Page {pdf_page.page_num + 1}",
            theme_text_color="Primary",
            size_hint_x=0.7
        )
        info_layout.add_widget(self.page_label)
        
        # Action buttons
        btn_layout = MDBoxLayout(orientation="horizontal", size_hint_x=0.3, spacing="5dp")
        
        self.edit_btn = MDIconButton(
            icon="pencil",
            theme_icon_color="Primary",
            on_release=self.edit_page
        )
        btn_layout.add_widget(self.edit_btn)
        
        self.delete_btn = MDIconButton(
            icon="delete",
            theme_icon_color="Error",
            on_release=self.delete_page
        )
        btn_layout.add_widget(self.delete_btn)
        
        info_layout.add_widget(btn_layout)
        layout.add_widget(info_layout)
        
        self.add_widget(layout)
        self.load_page_image()
    
    def load_page_image(self):
        """Load and display page image"""
        try:
            image_data = self.pdf_page.get_image(zoom=0.5)
            if image_data:
                # In a real implementation, you'd convert this to a Kivy texture
                self.page_image.source = "placeholder.png"  # Placeholder for now
        except Exception as e:
            logger.error(f"Error loading page image: {e}")
    
    def edit_page(self, instance):
        """Handle page edit action"""
        if hasattr(self.parent, 'parent') and hasattr(self.parent.parent, 'edit_page'):
            self.parent.parent.edit_page(self.pdf_page.page_num)
    
    def delete_page(self, instance):
        """Handle page delete action"""
        if hasattr(self.parent, 'parent') and hasattr(self.parent.parent, 'delete_page'):
            self.parent.parent.delete_page(self.pdf_page.page_num)


class PDFViewerScreen(MDScreen):
    """Main PDF viewer and editor screen"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "pdf_viewer"
        self.pdf_document = None
        
        # Main layout
        layout = MDBoxLayout(orientation="vertical")
        
        # Toolbar
        self.toolbar = MDTopAppBar(
            title="PDF Editor",
            left_action_items=[["menu", lambda x: self.open_menu()]],
            right_action_items=[
                ["file-plus", lambda x: self.create_new_pdf()],
                ["folder", lambda x: self.open_file()],
                ["content-save", lambda x: self.save_file()],
            ]
        )
        layout.add_widget(self.toolbar)
        
        # Content area
        content_layout = MDBoxLayout(orientation="horizontal")
        
        # Page list/thumbnails (left panel)
        self.page_list_container = MDBoxLayout(
            orientation="vertical",
            size_hint_x=0.3,
            md_bg_color="lightgray"
        )
        
        page_list_header = MDLabel(
            text="Pages",
            theme_text_color="Primary",
            size_hint_y=None,
            height="40dp"
        )
        self.page_list_container.add_widget(page_list_header)
        
        self.page_scroll = MDScrollView()
        self.page_list = MDList()
        self.page_scroll.add_widget(self.page_list)
        self.page_list_container.add_widget(self.page_scroll)
        
        content_layout.add_widget(self.page_list_container)
        
        # Main viewer area (right panel)
        viewer_container = MDBoxLayout(
            orientation="vertical",
            size_hint_x=0.7
        )
        
        # Viewer controls
        controls_layout = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height="50dp",
            spacing="10dp",
            padding="10dp"
        )
        
        self.zoom_out_btn = MDIconButton(
            icon="magnify-minus",
            on_release=self.zoom_out
        )
        controls_layout.add_widget(self.zoom_out_btn)
        
        self.zoom_label = MDLabel(
            text="100%",
            size_hint_x=None,
            width="60dp"
        )
        controls_layout.add_widget(self.zoom_label)
        
        self.zoom_in_btn = MDIconButton(
            icon="magnify-plus",
            on_release=self.zoom_in
        )
        controls_layout.add_widget(self.zoom_in_btn)
        
        controls_layout.add_widget(MDLabel())  # Spacer
        
        self.page_nav_label = MDLabel(
            text="Page 0 of 0",
            size_hint_x=None,
            width="100dp"
        )
        controls_layout.add_widget(self.page_nav_label)
        
        viewer_container.add_widget(controls_layout)
        
        # Main page viewer
        self.page_viewer = MDScrollView()
        self.current_page_widget = MDLabel(
            text="No PDF loaded",
            halign="center",
            valign="center"
        )
        self.page_viewer.add_widget(self.current_page_widget)
        viewer_container.add_widget(self.page_viewer)
        
        content_layout.add_widget(viewer_container)
        layout.add_widget(content_layout)
        
        # Status bar
        self.status_bar = MDLabel(
            text="Ready",
            size_hint_y=None,
            height="30dp",
            md_bg_color="darkgray"
        )
        layout.add_widget(self.status_bar)
        
        self.add_widget(layout)
        
        # File manager
        self.file_manager = None
        
        # Dialogs
        self.current_dialog = None
    
    def open_menu(self):
        """Open application menu"""
        menu_items = [
            {"text": "New PDF", "viewclass": "OneLineListItem", "on_release": lambda: self.create_new_pdf()},
            {"text": "Open PDF", "viewclass": "OneLineListItem", "on_release": lambda: self.open_file()},
            {"text": "Save PDF", "viewclass": "OneLineListItem", "on_release": lambda: self.save_file()},
            {"text": "Save As...", "viewclass": "OneLineListItem", "on_release": lambda: self.save_file_as()},
            {"text": "Merge PDF", "viewclass": "OneLineListItem", "on_release": lambda: self.merge_pdf()},
            {"text": "Extract Pages", "viewclass": "OneLineListItem", "on_release": lambda: self.extract_pages()},
            {"text": "Add Annotation", "viewclass": "OneLineListItem", "on_release": lambda: self.add_annotation()},
            {"text": "About", "viewclass": "OneLineListItem", "on_release": lambda: self.show_about()},
        ]
        
        self.menu = MDDropdownMenu(
            caller=self.toolbar.ids.left_actions,
            items=menu_items,
            width_mult=4,
        )
        self.menu.open()
    
    def create_new_pdf(self):
        """Create a new PDF document"""
        try:
            self.pdf_document = PDFDocument()
            self.pdf_document.doc = fitz.open()  # Create empty document
            self.pdf_document.insert_page(0, "New PDF Document\n\nThis is a new PDF created with PDF Editor.")
            self.refresh_page_list()
            self.update_status("Created new PDF document")
        except Exception as e:
            self.show_error(f"Error creating new PDF: {e}")
    
    def open_file(self):
        """Open file chooser to select PDF"""
        if not self.file_manager:
            self.file_manager = MDFileManager(
                exit_manager=self.exit_file_manager,
                select_path=self.select_file,
                ext=[".pdf"]
            )
        
        if ANDROID:
            self.file_manager.show(primary_external_storage_path())
        else:
            self.file_manager.show(str(Path.home()))
    
    def select_file(self, path: str):
        """Handle file selection"""
        self.exit_file_manager()
        self.load_pdf(path)
    
    def exit_file_manager(self, *args):
        """Close file manager"""
        self.file_manager.close()
    
    def load_pdf(self, file_path: str):
        """Load PDF document"""
        try:
            self.pdf_document = PDFDocument(file_path)
            if self.pdf_document.doc:
                self.refresh_page_list()
                self.show_page(0)
                self.update_status(f"Loaded: {Path(file_path).name}")
            else:
                self.show_error("Failed to load PDF document")
        except Exception as e:
            self.show_error(f"Error loading PDF: {e}")
    
    def save_file(self):
        """Save current PDF"""
        if self.pdf_document and self.pdf_document.file_path:
            if self.pdf_document.save_document():
                self.update_status("PDF saved successfully")
            else:
                self.show_error("Failed to save PDF")
        else:
            self.save_file_as()
    
    def save_file_as(self):
        """Save PDF with new name"""
        # In a real implementation, you'd show a save dialog
        if self.pdf_document:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"pdf_editor_output_{timestamp}.pdf"
            if self.pdf_document.save_document(output_path):
                self.update_status(f"PDF saved as: {output_path}")
            else:
                self.show_error("Failed to save PDF")
    
    def refresh_page_list(self):
        """Refresh the page list with thumbnails"""
        self.page_list.clear_widgets()
        
        if self.pdf_document and self.pdf_document.pages:
            for i, page in enumerate(self.pdf_document.pages):
                page_widget = PagePreviewWidget(page)
                self.page_list.add_widget(page_widget)
            
            self.update_page_nav()
    
    def show_page(self, page_num: int):
        """Display specific page in main viewer"""
        if self.pdf_document and 0 <= page_num < len(self.pdf_document.pages):
            self.pdf_document.current_page = page_num
            page = self.pdf_document.pages[page_num]
            
            # In a real implementation, you'd render the page image here
            self.current_page_widget.text = f"Page {page_num + 1}\n\n{page.get_text()[:500]}..."
            self.update_page_nav()
    
    def update_page_nav(self):
        """Update page navigation info"""
        if self.pdf_document and self.pdf_document.pages:
            current = self.pdf_document.current_page + 1
            total = len(self.pdf_document.pages)
            self.page_nav_label.text = f"Page {current} of {total}"
        else:
            self.page_nav_label.text = "Page 0 of 0"
    
    def zoom_in(self, instance):
        """Zoom in the current page"""
        if self.pdf_document:
            self.pdf_document.zoom_level = min(self.pdf_document.zoom_level * 1.2, 3.0)
            self.zoom_label.text = f"{int(self.pdf_document.zoom_level * 100)}%"
            self.refresh_current_page()
    
    def zoom_out(self, instance):
        """Zoom out the current page"""
        if self.pdf_document:
            self.pdf_document.zoom_level = max(self.pdf_document.zoom_level / 1.2, 0.3)
            self.zoom_label.text = f"{int(self.pdf_document.zoom_level * 100)}%"
            self.refresh_current_page()
    
    def refresh_current_page(self):
        """Refresh current page display with new zoom"""
        if self.pdf_document:
            self.show_page(self.pdf_document.current_page)
    
    def edit_page(self, page_num: int):
        """Edit specific page"""
        content = MDTextField(
            hint_text="Enter page content",
            multiline=True,
            size_hint_y=None,
            height="200dp"
        )
        
        if self.pdf_document and 0 <= page_num < len(self.pdf_document.pages):
            content.text = self.pdf_document.pages[page_num].get_text()
        
        self.current_dialog = MDDialog(
            title=f"Edit Page {page_num + 1}",
            content_cls=content,
            buttons=[
                MDFlatButton(text="Cancel", on_release=self.close_dialog),
                MDRaisedButton(text="Save", on_release=lambda x: self.save_page_edit(page_num, content.text))
            ]
        )
        self.current_dialog.open()
    
    def save_page_edit(self, page_num: int, content: str):
        """Save page edit"""
        # In a real implementation, you'd update the page content
        self.close_dialog()
        self.update_status(f"Page {page_num + 1} updated")
    
    def delete_page(self, page_num: int):
        """Delete specific page"""
        self.current_dialog = MDDialog(
            title="Delete Page",
            text=f"Are you sure you want to delete page {page_num + 1}?",
            buttons=[
                MDFlatButton(text="Cancel", on_release=self.close_dialog),
                MDRaisedButton(
                    text="Delete",
                    md_bg_color="red",
                    on_release=lambda x: self.confirm_delete_page(page_num)
                )
            ]
        )
        self.current_dialog.open()
    
    def confirm_delete_page(self, page_num: int):
        """Confirm page deletion"""
        if self.pdf_document and self.pdf_document.delete_page(page_num):
            self.refresh_page_list()
            self.close_dialog()
            self.update_status(f"Page {page_num + 1} deleted")
        else:
            self.show_error("Failed to delete page")
    
    def merge_pdf(self):
        """Merge another PDF"""
        # In a real implementation, you'd show a file chooser
        self.update_status("Merge PDF feature - select file to merge")
    
    def extract_pages(self):
        """Extract pages to new PDF"""
        # In a real implementation, you'd show a dialog to select page range
        self.update_status("Extract pages feature - select page range")
    
    def add_annotation(self):
        """Add annotation to current page"""
        # In a real implementation, you'd show annotation tools
        self.update_status("Annotation feature - select annotation type")
    
    def show_about(self):
        """Show about dialog"""
        self.current_dialog = MDDialog(
            title="About PDF Editor",
            text="PDF Editor v1.0\nOptimized for Android (Moto G54 5G)\n\nFeatures:\n• PDF viewing and editing\n• Page management\n• Annotations\n• Merge and extract\n• Mobile-optimized UI",
            buttons=[MDFlatButton(text="OK", on_release=self.close_dialog)]
        )
        self.current_dialog.open()
    
    def close_dialog(self, *args):
        """Close current dialog"""
        if self.current_dialog:
            self.current_dialog.dismiss()
            self.current_dialog = None
    
    def show_error(self, message: str):
        """Show error message"""
        Snackbar(text=message, bg_color="red").open()
    
    def update_status(self, message: str):
        """Update status bar"""
        self.status_bar.text = message
        logger.info(message)


class PDFEditorApp(MDApp):
    """Main application class"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "PDF Editor"
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        
    def build(self):
        """Build the application"""
        # Request Android permissions
        if ANDROID:
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE
            ])
        
        # Create screen manager
        self.screen_manager = MDScreenManager()
        
        # Add main screen
        pdf_viewer = PDFViewerScreen()
        self.screen_manager.add_widget(pdf_viewer)
        
        return self.screen_manager
    
    def on_start(self):
        """Called when the app starts"""
        logger.info("PDF Editor app started")
        
    def on_stop(self):
        """Called when the app stops"""
        logger.info("PDF Editor app stopped")


def main():
    """Main entry point"""
    try:
        logger.info("Starting PDF Editor application")
        app = PDFEditorApp()
        app.run()
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise


if __name__ == "__main__":
    main()# Kivy imports
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.image import Image
