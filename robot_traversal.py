import tkinter as tk
from tkinter import messagebox, filedialog
import json
from maze_solver import MazeSolver
from maze_generator import MazeGenerator

class RobotTraversal:
    def __init__(self, root):
        self.root = root
        self.root.title("Robot Traversal")
        self.default_rows = 20
        self.default_cols = 20
        self.default_density = 100
        self.rows = self.default_rows
        self.cols = self.default_cols
        self.cell_size = 20
        self.walls = {}
        self.robot_pos = (self.cols // 2, self.rows // 2)
        self.start_pos = self.robot_pos
        self.robot_dir = 'NORTH'
        self.visited = {}
        self.scanned_cells = set()
        self.speed = 150
        self.traversal_path = []
        self.current_step = 0
        self.steps_count = 0
        self.turns_count = 0
        self.is_paused = False
        self.auto_traverse_id = None
        self.in_auto_mode = False
        self.density = self.default_density
        self.has_maze = False
        self.offset_x = 0
        self.offset_y = 0
        self.create_widgets()
        self.initialize_game()

    def create_widgets(self):
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.left_frame = tk.Frame(self.main_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.right_frame = tk.Frame(self.main_frame, width=150)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.button_panel = tk.Frame(self.right_frame)
        self.button_panel.pack(fill=tk.X, padx=5, pady=5)

        buttons = [
            ("Лабиринт", self.generate_maze),
            ("Очистить", self.clear_field),
            ("Сброс", self.reset_field),
            ("Сохранить", self.save_maze),
            ("Загрузить", self.load_maze),
            ("Влево", lambda: self.turn_robot("LEFT")),
            ("Вправо", lambda: self.turn_robot("RIGHT")),
            ("Шаг", self.manual_move),
            ("Авто", self.toggle_auto_traverse),
            ("Пауза", self.toggle_pause_resume),
            ("Быстрее", self.speed_up),
            ("Медленнее", self.slow_down),
        ]

        for i, (text, command) in enumerate(buttons):
            btn = tk.Button(self.button_panel, text=text, command=command, width=8)
            btn.grid(row=i//2, column=i%2, padx=2, pady=2, sticky="ew")

        self.button_panel.grid_columnconfigure(0, weight=1)
        self.button_panel.grid_columnconfigure(1, weight=1)

        self.settings_panel = tk.Frame(self.right_frame)
        self.settings_panel.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(self.settings_panel, text="Верт:").grid(row=0, column=0, sticky=tk.W)
        self.rows_entry = tk.Entry(self.settings_panel, width=5)
        self.rows_entry.grid(row=0, column=1, sticky=tk.W)
        self.rows_entry.insert(0, str(self.default_rows))

        tk.Label(self.settings_panel, text="Гор:").grid(row=1, column=0, sticky=tk.W)
        self.cols_entry = tk.Entry(self.settings_panel, width=5)
        self.cols_entry.grid(row=1, column=1, sticky=tk.W)
        self.cols_entry.insert(0, str(self.default_cols))

        tk.Label(self.settings_panel, text="Плотность (%):").grid(row=2, column=0, sticky=tk.W)
        self.density_entry = tk.Entry(self.settings_panel, width=5)
        self.density_entry.grid(row=2, column=1, sticky=tk.W)
        self.density_entry.insert(0, str(self.default_density))

        self.apply_btn = tk.Button(self.settings_panel, text="Применить", command=self.apply_settings)
        self.apply_btn.grid(row=3, column=0, columnspan=2, pady=5)

        self.status_panel = tk.Frame(self.right_frame)
        self.status_panel.pack(fill=tk.X, padx=5, pady=5)

        self.status_row1 = tk.Frame(self.status_panel)
        self.status_row1.pack(fill=tk.X)
        self.steps_label = tk.Label(self.status_row1, text="Шаги: 0")
        self.steps_label.pack(side=tk.LEFT, padx=5)
        self.turns_label = tk.Label(self.status_row1, text="Повороты: 0")
        self.turns_label.pack(side=tk.LEFT, padx=5)

        self.status_row2 = tk.Frame(self.status_panel)
        self.status_row2.pack(fill=tk.X)
        self.speed_label = tk.Label(self.status_row2, text=f"Скорость: {self.speed}")
        self.speed_label.pack(side=tk.LEFT, padx=5)

        self.status_row3 = tk.Frame(self.status_panel)
        self.status_row3.pack(fill=tk.X)
        self.paths_label = tk.Label(self.status_row3, text="Пути: 0")
        self.paths_label.pack(side=tk.LEFT, padx=5)

        self.canvas = tk.Canvas(self.left_frame, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.toggle_wall)
        self.canvas.bind("<Button-3>", self.move_robot_to_cell)
        self.canvas.bind("<Configure>", self.on_canvas_resize)

    def on_canvas_resize(self, event):
        canvas_width = event.width
        canvas_height = event.height
        if canvas_width > 10 and canvas_height > 10:
            self.cell_size = min(
                (canvas_width - 40) // max(1, self.cols),
                (canvas_height - 40) // max(1, self.rows)
            )
            self.cell_size = max(5, self.cell_size)
            self.draw_field()

    def apply_settings(self):
        try:
            new_rows = int(self.rows_entry.get())
            new_cols = int(self.cols_entry.get())
            new_density = int(self.density_entry.get())
            
            if new_rows < 1 or new_cols < 1 or new_density < 0 or new_density > 100:
                raise ValueError
            
            old_rows = self.rows
            old_cols = self.cols
            self.rows = new_rows
            self.cols = new_cols
            self.density = new_density
            
            rx, ry = self.robot_pos
            left_cols = rx
            right_cols = old_cols - rx - 1
            top_rows = ry
            bottom_rows = old_rows - ry - 1
            
            col_diff = new_cols - old_cols
            row_diff = new_rows - old_rows
            
            if col_diff % 2 == 0:
                col_shift_left = col_shift_right = col_diff // 2
            else:
                if col_diff > 0:
                    if left_cols <= right_cols:
                        col_shift_left = col_diff // 2
                        col_shift_right = col_diff - col_shift_left
                    else:
                        col_shift_right = col_diff // 2
                        col_shift_left = col_diff - col_shift_right
                else:
                    if left_cols >= right_cols:
                        col_shift_left = col_diff // 2
                        col_shift_right = col_diff - col_shift_left
                    else:
                        col_shift_right = col_diff // 2
                        col_shift_left = col_diff - col_shift_right
            
            if row_diff % 2 == 0:
                row_shift_top = row_shift_bottom = row_diff // 2
            else:
                if row_diff > 0:
                    if top_rows <= bottom_rows:
                        row_shift_top = row_diff // 2
                        row_shift_bottom = row_diff - row_shift_top
                    else:
                        row_shift_bottom = row_diff // 2
                        row_shift_top = row_diff - row_shift_bottom
                else:
                    if top_rows >= bottom_rows:
                        row_shift_top = row_diff // 2
                        row_shift_bottom = row_diff - row_shift_top
                    else:
                        row_shift_bottom = row_diff // 2
                        row_shift_top = row_shift_bottom
            
            new_rx = rx + col_shift_left
            new_ry = ry + row_shift_top
            if new_rx < 0 or new_rx >= self.cols or new_ry < 0 or new_ry >= self.rows:
                new_rx = self.cols // 2
                new_ry = self.rows // 2
            self.robot_pos = (new_rx, new_ry)
            self.start_pos = self.robot_pos
            
            new_walls = {}
            for wall, state in self.walls.items():
                (x1, y1), (x2, y2) = wall
                new_x1 = x1 + col_shift_left
                new_y1 = y1 + row_shift_top
                new_x2 = x2 + col_shift_left
                new_y2 = y2 + row_shift_top
                if (0 <= new_x1 < self.cols and 0 <= new_y1 < self.rows and
                    0 <= new_x2 < self.cols and 0 <= new_y2 < self.rows):
                    new_walls[((new_x1, new_y1), (new_x2, new_y2))] = state
            self.walls = new_walls
            
            new_visited = {}
            for pos, count in self.visited.items():
                x, y = pos
                new_x = x + col_shift_left
                new_y = y + row_shift_top
                if 0 <= new_x < self.cols and 0 <= new_y < self.rows:
                    new_visited[(new_x, new_y)] = count
            if (new_rx, new_ry) not in new_visited:
                new_visited[(new_rx, new_ry)] = 1
            self.visited = new_visited

            self.steps_count = 0
            self.turns_count = 0
            self.has_maze = False
            self.update_status()
            self.scan_environment()
            self.draw_field()
            
        except ValueError:
            messagebox.showerror("Ошибка", "Пожалуйста, введите корректные значения\n(Верт. и Гор. - целые > 0, Плотность 0-100)")
            self.rows_entry.delete(0, tk.END)
            self.rows_entry.insert(0, str(self.rows))
            self.cols_entry.delete(0, tk.END)
            self.cols_entry.insert(0, str(self.cols))
            self.density_entry.delete(0, tk.END)
            self.density_entry.insert(0, str(self.density))

    def initialize_game(self):
        self.visited[self.robot_pos] = 1
        self.scan_environment()
        self.draw_field()

    def draw_field(self):
        self.canvas.delete("all")
        
        field_width = self.cols * self.cell_size
        field_height = self.rows * self.cell_size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        self.offset_x = (canvas_width - field_width) // 2 if canvas_width > field_width else 0
        self.offset_y = (canvas_height - field_height) // 2 if canvas_height > field_height else 0
        
        for y in range(self.rows):
            for x in range(self.cols):
                visit_count = self.visited.get((x, y), 0)
                
                if (x, y) == self.robot_pos:
                    base_color = "blue"
                elif (x, y) in self.scanned_cells and visit_count == 0:
                    base_color = "yellow"
                elif visit_count > 0:
                    base_color = "#00FF00" if visit_count == 1 else \
                                "#FFA500" if visit_count == 2 else \
                                "#800080" if visit_count == 3 else \
                                "#FF0000" if visit_count >= 4 else "#FFFFFF"
                else:
                    base_color = "white"
                    
                self.canvas.create_rectangle(
                    self.offset_x + x * self.cell_size, self.offset_y + y * self.cell_size,
                    self.offset_x + (x + 1) * self.cell_size, self.offset_y + (y + 1) * self.cell_size,
                    fill=base_color, outline="gray"
                )
                
                if visit_count > 0 and (x, y) != self.robot_pos:
                    self.canvas.create_text(
                        self.offset_x + x * self.cell_size + self.cell_size//2,
                        self.offset_y + y * self.cell_size + self.cell_size//2,
                        text=str(visit_count),
                        fill="black" if visit_count <= 2 else "white"
                    )
        
        for (x1, y1), (x2, y2) in self.walls:
            if self.walls[((x1, y1), (x2, y2))]:
                if x1 == x2 and 0 <= y1 < self.rows and 0 <= y2 <= self.rows:
                    y = max(y1, y2)
                    self.canvas.create_line(
                        self.offset_x + x1 * self.cell_size, self.offset_y + y * self.cell_size,
                        self.offset_x + (x1 + 1) * self.cell_size, self.offset_y + y * self.cell_size,
                        width=3, fill="black"
                    )
                elif y1 == y2 and 0 <= x1 < self.cols and 0 <= x2 <= self.cols:
                    x = max(x1, x2)
                    self.canvas.create_line(
                        self.offset_x + x * self.cell_size, self.offset_y + y1 * self.cell_size,
                        self.offset_x + x * self.cell_size, self.offset_y + (y1 + 1) * self.cell_size,
                        width=3, fill="black"
                    )
        
        self.draw_robot()
        self.update_status()

    def draw_robot(self):
        x, y = self.robot_pos
        size = self.cell_size
        half = size // 2
        quarter = size // 4
        
        directions = {
            'NORTH': [
                self.offset_x + x * size + half, self.offset_y + y * size + quarter,
                self.offset_x + x * size + quarter, self.offset_y + y * size + 3 * quarter,
                self.offset_x + x * size + 3 * quarter, self.offset_y + y * size + 3 * quarter
            ],
            'EAST': [
                self.offset_x + x * size + 3 * quarter, self.offset_y + y * size + half,
                self.offset_x + x * size + quarter, self.offset_y + y * size + quarter,
                self.offset_x + x * size + quarter, self.offset_y + y * size + 3 * quarter
            ],
            'SOUTH': [
                self.offset_x + x * size + half, self.offset_y + y * size + 3 * quarter,
                self.offset_x + x * size + quarter, self.offset_y + y * size + quarter,
                self.offset_x + x * size + 3 * quarter, self.offset_y + y * size + quarter
            ],
            'WEST': [
                self.offset_x + x * size + quarter, self.offset_y + y * size + half,
                self.offset_x + x * size + 3 * quarter, self.offset_y + y * size + quarter,
                self.offset_x + x * size + 3 * quarter, self.offset_y + y * size + 3 * quarter
            ]
        }
        
        self.canvas.create_polygon(
            directions[self.robot_dir], 
            fill="white", 
            outline="black"
        )

    def scan_environment(self):
        self.scanned_cells.clear()
        for pos in self.visited:
            x, y = pos
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows and (nx, ny) not in self.visited:
                    wall_key = ((x, y), (nx, ny)) if (x, y) < (nx, ny) else ((nx, ny), (x, y))
                    if not self.walls.get(wall_key, False):
                        self.scanned_cells.add((nx, ny))

    def update_status(self):
        self.steps_label.config(text=f"Шаги: {self.steps_count}")
        self.turns_label.config(text=f"Повороты: {self.turns_count}")
        self.speed_label.config(text=f"Скорость: {self.speed}")
        self.paths_label.config(text=f"Пути: {len(self.scanned_cells)}")

    def generate_maze(self):
        self.clear_field()
        try:
            density = int(self.density_entry.get()) / 100
        except ValueError:
            density = self.density / 100
        
        density = max(0, min(1, density))
        
        generator = MazeGenerator(self.rows, self.cols, density)
        generator.generate_maze_kruskal()
        self.walls = generator.get_walls()
        self.has_maze = True
        self.scan_environment()
        self.draw_field()

    def clear_field(self):
        self.walls = {}
        self.visited = {self.robot_pos: 1}
        self.scanned_cells = set()
        self.steps_count = 0
        self.turns_count = 0
        self.has_maze = False
        self.update_status()
        self.scan_environment()
        self.draw_field()

    def reset_field(self):
        self.clear_field()
        self.robot_pos = (self.cols // 2, self.rows // 2)
        self.start_pos = self.robot_pos
        self.robot_dir = 'NORTH'
        self.visited = {self.robot_pos: 1}
        if self.auto_traverse_id:
            self.root.after_cancel(self.auto_traverse_id)
            self.auto_traverse_id = None
        self.traversal_path = []
        self.current_step = 0
        self.is_paused = False
        self.in_auto_mode = False
        self.update_status()
        self.scan_environment()
        self.draw_field()

    def toggle_wall(self, event):
        x = int((event.x - self.offset_x) // self.cell_size)
        y = int((event.y - self.offset_y) // self.cell_size)
        
        rel_x = ((event.x - self.offset_x) % self.cell_size) / self.cell_size
        rel_y = ((event.y - self.offset_y) % self.cell_size) / self.cell_size
        
        if rel_x < 0.2 and x > 0:
            wall_key = ((x-1, y), (x, y))
        elif rel_x > 0.8 and x < self.cols - 1:
            wall_key = ((x, y), (x+1, y))
        elif rel_y < 0.2 and y > 0:
            wall_key = ((x, y-1), (x, y))
        elif rel_y > 0.8 and y < self.rows - 1:
            wall_key = ((x, y), (x, y+1))
        else:
            return
        
        self.walls[wall_key] = not self.walls.get(wall_key, False)
        self.scan_environment()
        self.draw_field()

    def move_robot_to_cell(self, event):
        x = int((event.x - self.offset_x) // self.cell_size)
        y = int((event.y - self.offset_y) // self.cell_size)
        
        if 0 <= x < self.cols and 0 <= y < self.rows:
            path = self.find_path(self.robot_pos, (x, y))
            if path:
                self.robot_pos = (x, y)
                self.visited[(x, y)] = self.visited.get((x, y), 0) + 1
                self.scan_environment()
                self.draw_field()
            else:
                messagebox.showinfo("Ошибка", "Невозможно переместить робота - путь заблокирован стенами")

    def find_path(self, start, end):
        queue = [(start, [start])]
        visited = set()
        
        while queue:
            (x, y), path = queue.pop(0)
            if (x, y) == end:
                return path
                
            if (x, y) in visited:
                continue
            visited.add((x, y))
            
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    wall_key = ((x, y), (nx, ny)) if (x, y) < (nx, ny) else ((nx, ny), (x, y))
                    if not self.walls.get(wall_key, False) and (nx, ny) not in visited:
                        queue.append(((nx, ny), path + [(nx, ny)]))
        return None

    def turn_robot(self, direction):
        directions = {
            'NORTH': {'LEFT': 'WEST', 'RIGHT': 'EAST'},
            'EAST': {'LEFT': 'NORTH', 'RIGHT': 'SOUTH'},
            'SOUTH': {'LEFT': 'EAST', 'RIGHT': 'WEST'},
            'WEST': {'LEFT': 'SOUTH', 'RIGHT': 'NORTH'}
        }
        self.robot_dir = directions[self.robot_dir][direction]
        self.turns_count += 1
        self.update_status()
        self.scan_environment()
        self.draw_field()

    def manual_move(self):
        x, y = self.robot_pos
        direction_offsets = {
            'NORTH': (0, -1),
            'EAST': (1, 0),
            'SOUTH': (0, 1),
            'WEST': (-1, 0)
        }
        dx, dy = direction_offsets[self.robot_dir]
        new_x, new_y = x + dx, y + dy

        wall_key = ((x, y), (new_x, new_y)) if (x, y) < (new_x, new_y) else ((new_x, new_y), (x, y))
        
        if (0 <= new_x < self.cols and 0 <= new_y < self.rows and 
            not self.walls.get(wall_key, False)):
            self.robot_pos = (new_x, new_y)
            self.visited[(new_x, new_y)] = self.visited.get((new_x, new_y), 0) + 1
            self.steps_count += 1
            self.scan_environment()
        else:
            messagebox.showinfo("Препятствие", "Невозможно двигаться вперёд. Обнаружена стена.")

        self.update_status()
        self.draw_field()

    def toggle_auto_traverse(self):
        if not self.traversal_path:
            self.start_auto_traverse()
        elif self.is_paused:
            self.resume_auto_traverse()
        else:
            self.pause_auto_traverse()

    def start_auto_traverse(self):
        self.in_auto_mode = True
        self.traversal_path = []
        self.current_step = 0
        self.is_paused = False
        self.auto_traverse_step()

    def auto_traverse_step(self):
        if not self.scanned_cells and not self.traversal_path[self.current_step:]:
            self.in_auto_mode = False
            messagebox.showinfo("Завершено", "Путешествие завершено.")
            return

        if self.is_paused:
            return

        if self.current_step >= len(self.traversal_path):
            solver = MazeSolver(self.walls, self.rows, self.cols, self.robot_pos, self.robot_dir, self.visited, self.start_pos)
            solver.scanned_cells = self.scanned_cells.copy()
            path = []
            step = solver.get_next_step()
            while step:
                path.append(step)
                step = solver.get_next_step()
            self.traversal_path = path
            self.current_step = 0
            if not self.traversal_path:
                self.in_auto_mode = False
                messagebox.showinfo("Завершено", "Путешествие завершено.")
                return

        x, y, direction = self.traversal_path[self.current_step]
        
        if direction != self.robot_dir:
            self.robot_dir = direction
            self.turns_count += 1
            self.update_status()
            self.draw_field()
            self.current_step += 1
            self.auto_traverse_id = self.root.after(self.speed, self.auto_traverse_step)
            return
        
        if (x, y) != self.robot_pos:
            self.robot_pos = (x, y)
            self.visited[(x, y)] = self.visited.get((x, y), 0) + 1
            self.steps_count += 1
            self.scan_environment()
        
        self.update_status()
        self.draw_field()
        self.current_step += 1
        self.auto_traverse_id = self.root.after(self.speed, self.auto_traverse_step)

    def toggle_pause_resume(self):
        if self.is_paused:
            self.resume_auto_traverse()
        else:
            self.pause_auto_traverse()

    def pause_auto_traverse(self):
        if self.auto_traverse_id:
            self.is_paused = True
            self.root.after_cancel(self.auto_traverse_id)
            self.auto_traverse_id = None

    def resume_auto_traverse(self):
        if self.is_paused and self.traversal_path:
            self.is_paused = False
            self.auto_traverse_step()

    def speed_up(self):
        self.speed = max(50, self.speed - 50)
        self.speed_label.config(text=f"Скорость: {self.speed}")

    def slow_down(self):
        self.speed = min(300, self.speed + 50)
        self.speed_label.config(text=f"Скорость: {self.speed}")

    def save_maze(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if filename:
            data = {
                "rows": self.rows,
                "cols": self.cols,
                "walls": [list(pair) for pair in self.walls.items()],
                "robot_pos": self.robot_pos,
                "start_pos": self.start_pos,
                "robot_dir": self.robot_dir,
                "visited": list(self.visited.items()),
                "steps": self.steps_count,
                "turns": self.turns_count,
                "density": self.density
            }
            with open(filename, "w") as f:
                json.dump(data, f)

    def load_maze(self):
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")]
        )
        if filename:
            with open(filename, "r") as f:
                data = json.load(f)
                self.rows = data["rows"]
                self.cols = data["cols"]
                self.walls = {tuple(tuple(p) for p in k): v for k, v in data["walls"]}
                self.robot_pos = tuple(data["robot_pos"])
                self.start_pos = tuple(data["start_pos"])
                self.robot_dir = data["robot_dir"]
                self.visited = dict(tuple(item) for item in data.get("visited", []))
                self.steps_count = data.get("steps", 0)
                self.turns_count = data.get("turns", 0)
                self.density = data.get("density", self.default_density)
                
                self.rows_entry.delete(0, tk.END)
                self.rows_entry.insert(0, str(self.rows))
                self.cols_entry.delete(0, tk.END)
                self.cols_entry.insert(0, str(self.cols))
                self.density_entry.delete(0, tk.END)
                self.density_entry.insert(0, str(self.density))
                
                self.has_maze = True
                self.update_status()
                self.scan_environment()
                self.draw_field()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")
    app = RobotTraversal(root)
    root.mainloop()