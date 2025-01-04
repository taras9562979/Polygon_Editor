import sys
import math
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton, 
                            QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                            QFileDialog, QMessageBox)
from PyQt6.QtGui import QPainter, QColor, QPen, QImage
from PyQt6.QtCore import Qt, QPoint, QRect

# Global state
nodes = []  # List of tuples: (center: QPoint, radius: int, sides: int)
connections = []  # List of tuples: (start_index: int, end_index: int)
current_mode = None  # Initially no mode is active
radius = 30
sides = 5
selected_polygon = None
offset = QPoint()
connection_start = None
canvas_widget = None  # Will store reference to canvas widget

def calculate_polygon_coords(center, radius, sides):
    """Calculate the coordinates of a regular polygon."""
    points = []
    for i in range(sides):
        angle = (2 * math.pi / sides) * i
        x = center.x() + radius * math.cos(angle)
        y = center.y() + radius * math.sin(angle)
        points.append(QPoint(int(x), int(y)))
    return points

def paint_canvas(painter, event_rect):
    """Paint all polygons and connections on the canvas."""
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Set background color
    painter.fillRect(event_rect, QColor('lightblue'))
    
    # Draw connections
    pen = QPen(QColor('red'))
    pen.setWidth(2)
    painter.setPen(pen)
    for start_idx, end_idx in connections:
        start_center = nodes[start_idx][0]
        end_center = nodes[end_idx][0]
        painter.drawLine(start_center, end_center)
    
    # Draw polygons
    pen = QPen(QColor('black'))
    pen.setWidth(2)
    painter.setPen(pen)
    painter.setBrush(QColor('blue'))
    
    for center, radius, sides in nodes:
        points = calculate_polygon_coords(center, radius, sides)
        painter.drawPolygon(*points)

def handle_paint_event(event):
    """Handle the paint event for the canvas."""
    painter = QPainter(canvas_widget)
    paint_canvas(painter, event.rect())

def create_node(pos):
    """Create a new polygon at the specified position."""
    nodes.append((pos, radius, sides))
    canvas_widget.update()
    print("--------------------------------------------------------------------")
    print('After creation:')
    print('Nodes:', [(f"center: ({n[0].x()}, {n[0].y()})", f"radius: {n[1]}", f"sides: {n[2]}") for n in nodes])

def delete_node(pos):
    """Delete the polygon at the specified position."""
    global connections
    for i, (center, radius, _) in enumerate(nodes):
        if (pos - center).manhattanLength() <= radius:
            nodes.pop(i)
            # Remove connections involving this node
            connections = [(start, end) for start, end in connections 
                          if start != i and end != i]
            # Update indices in connections
            connections = [(start if start < i else start - 1,
                           end if end < i else end - 1)
                          for start, end in connections]
            canvas_widget.update()
            print("--------------------------------------------------------------------")
            print('After deletion:')
            print('Nodes:', [(f"center: ({n[0].x()}, {n[0].y()})", f"radius: {n[1]}", f"sides: {n[2]}") for n in nodes])
            print('Connections:', connections)
            return

def start_move(pos):
    """Start moving a polygon."""
    global selected_polygon, offset
    for i, (center, radius, _) in enumerate(nodes):
        if (pos - center).manhattanLength() <= radius:
            selected_polygon = i
            offset = pos - center
            return

def handle_move(pos):
    """Handle moving a selected polygon."""
    global nodes
    if selected_polygon is not None:
        new_pos = pos - offset
        nodes[selected_polygon] = (new_pos, radius, sides)
        canvas_widget.update()

def end_move():
    """End polygon movement."""
    global selected_polygon
    if selected_polygon is not None:  # Only print if we were actually moving a polygon
        print("--------------------------------------------------------------------")
        print('After moving:')
        print('Nodes:', [(f"center: ({n[0].x()}, {n[0].y()})", f"radius: {n[1]}", f"sides: {n[2]}") for n in nodes])
    selected_polygon = None

def handle_connect(pos):
    """Handle connecting polygons."""
    global connection_start, connections
    for i, (center, radius, _) in enumerate(nodes):
        if (pos - center).manhattanLength() <= radius:
            if connection_start is None:
                connection_start = i
                print("First polygon selected. Click another to connect.")
            else:
                if connection_start != i:
                    if (connection_start, i) not in connections and \
                       (i, connection_start) not in connections:
                        connections.append((connection_start, i))
                        canvas_widget.update()
                        print("--------------------------------------------------------------------")
                        print('After connecting:')
                        print('Connections:', connections)
                connection_start = None
            return

def handle_mouse_press(event):
    """Handle mouse press events based on current mode."""
    if event.button() == Qt.MouseButton.LeftButton and current_mode:  # Only handle if a mode is active
        pos = event.pos()
        if current_mode == "create":
            create_node(pos)
        elif current_mode == "delete":
            delete_node(pos)
        elif current_mode == "move":
            start_move(pos)
        elif current_mode == "connect":
            handle_connect(pos)

def handle_mouse_move(event):
    """Handle mouse move events."""
    if current_mode == "move":
        handle_move(event.pos())

def handle_mouse_release(event):
    """Handle mouse release events."""
    if current_mode == "move":
        end_move()

def set_mode(mode):
    """Set the current interaction mode."""
    global current_mode, connection_start
    current_mode = mode
    connection_start = None
    
    print("--------------------------------------------------------------------")
    if mode == "create":
        print("You are in Create Mode -> Left-click on the canvas to create a polygon")
    elif mode == "delete":
        print("You are in Delete Mode -> Left-click on a polygon to delete it")
    elif mode == "move":
        print("You are in Move Mode -> Left-click on a polygon and drag it to new location")
    elif mode == "connect":
        print("You are in Connect Mode -> Click two polygons to connect them")

def change_sides(new_sides):
    """Change the number of sides for new polygons."""
    global sides
    sides = int(new_sides)

def export_as_png(window):
    """Export the canvas as a PNG image."""
    filename, _ = QFileDialog.getSaveFileName(window, "Save Image", "", "PNG Files (*.png)")
    if filename:
        image = QImage(canvas_widget.size(), QImage.Format.Format_RGB32)
        painter = QPainter(image)
        canvas_widget.render(painter)
        painter.end()
        image.save(filename)

def save_arrangement(window):
    """Save the current arrangement to a JSON file."""
    filename, _ = QFileDialog.getSaveFileName(window, "Save Arrangement", "", "JSON Files (*.json)")
    if filename:
        arrangement = {
            "nodes": [({"x": node[0].x(), "y": node[0].y()}, node[1], node[2]) 
                     for node in nodes],
            "connections": connections
        }
        with open(filename, 'w') as f:
            json.dump(arrangement, f)

def load_arrangement(window):
    """Load an arrangement from a JSON file."""
    global nodes, connections
    filename, _ = QFileDialog.getOpenFileName(window, "Load Arrangement", "", "JSON Files (*.json)")
    if filename:
        with open(filename, 'r') as f:
            arrangement = json.load(f)
        
        nodes = [(QPoint(node[0]["x"], node[0]["y"]), node[1], node[2]) 
                 for node in arrangement["nodes"]]
        connections = arrangement["connections"]
        canvas_widget.update()

def create_canvas():
    """Create and return the canvas widget."""
    global canvas_widget
    
    canvas = QWidget()
    canvas.setMinimumSize(1200, 800)
    
    # Set up event handlers
    canvas.paintEvent = handle_paint_event
    canvas.mousePressEvent = handle_mouse_press
    canvas.mouseMoveEvent = handle_mouse_move
    canvas.mouseReleaseEvent = handle_mouse_release
    
    canvas_widget = canvas
    return canvas

def create_window():
    """Create and return the main application window."""
    window = QMainWindow()
    window.setWindowTitle("Polygon Editor")
    
    # Create main widget and layout
    main_widget = QWidget()
    window.setCentralWidget(main_widget)
    layout = QVBoxLayout(main_widget)
    
    # Create control panel
    control_panel = QWidget()
    control_layout = QHBoxLayout(control_panel)
    
    # Create mode buttons
    for mode in ["Create", "Delete", "Move", "Connect"]:
        button = QPushButton(f"{mode} Mode")
        button.clicked.connect(lambda checked, m=mode.lower(): set_mode(m))
        control_layout.addWidget(button)
    
    # Create sides selector
    control_layout.addWidget(QLabel("Number of Sides:"))
    sides_combo = QComboBox()
    sides_combo.addItems([str(i) for i in range(3, 21)])
    sides_combo.setCurrentText("5")
    sides_combo.currentTextChanged.connect(change_sides)
    control_layout.addWidget(sides_combo)
    
    # Create export/save/load buttons
    export_btn = QPushButton("Export as PNG")
    export_btn.clicked.connect(lambda: export_as_png(window))
    control_layout.addWidget(export_btn)
    
    save_btn = QPushButton("Save Arrangement")
    save_btn.clicked.connect(lambda: save_arrangement(window))
    control_layout.addWidget(save_btn)
    
    load_btn = QPushButton("Load Arrangement")
    load_btn.clicked.connect(lambda: load_arrangement(window))
    control_layout.addWidget(load_btn)
    
    layout.addWidget(control_panel)
    
    # Create and add canvas
    canvas = create_canvas()
    layout.addWidget(canvas)
    
    return window

def main():
    """Main entry point of the application."""
    app = QApplication(sys.argv)
    window = create_window()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
