from collections import deque
import heapq

class MazeSolver:
    def __init__(self, walls, rows, cols, start_pos, start_dir, visited, start_pos_original):
        self.walls = walls
        self.rows = rows
        self.cols = cols
        self.current_pos = start_pos
        self.current_dir = start_dir
        self.visited = visited.copy()
        self.start_pos = start_pos_original
        self.directions = ['NORTH', 'EAST', 'SOUTH', 'WEST']
        self.known_walls = {}
        self.scanned_cells = set()
        self.path = []
        self.path_index = 0
        self.scan_environment(start_pos)

    def scan_environment(self, pos):
        x, y = pos
        for dx, dy, _ in [(-1, 0, 'WEST'), (1, 0, 'EAST'), (0, -1, 'NORTH'), (0, 1, 'SOUTH')]:
            nx, ny = x + dx, y + dy
            wall_key = ((x, y), (nx, ny)) if (x, y) < (nx, ny) else ((nx, ny), (x, y))
            if nx < 0 or nx >= self.cols or ny < 0 or ny >= self.rows:
                self.known_walls[wall_key] = True
            else:
                self.known_walls[wall_key] = self.walls.get(wall_key, False)
                if not self.known_walls[wall_key] and (nx, ny) not in self.visited:
                    self.scanned_cells.add((nx, ny))

    def get_wall_count(self, x, y):
        wall_count = 0
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            wall_key = ((x, y), (nx, ny)) if (x, y) < (nx, ny) else ((nx, ny), (x, y))
            if nx < 0 or nx >= self.cols or ny < 0 or ny >= self.rows:
                wall_count += 1
            elif self.known_walls.get(wall_key, False):
                wall_count += 1
        return wall_count

    def initialize_path(self):
        self.path = []
        self.path_index = 0
        visited = set(self.visited.keys())
        current_x, current_y = self.current_pos
        current_dir = self.current_dir

        target = self.find_nearest_unvisited(current_x, current_y, visited)
        if not target:
            return

        move_path = self.a_star((current_x, current_y), target, visited)
        if not move_path:
            return

        for step in move_path:
            step_x, step_y = step
            if step_x > current_x:
                step_dir = 'EAST'
            elif step_x < current_x:
                step_dir = 'WEST'
            elif step_y > current_y:
                step_dir = 'SOUTH'
            else:
                step_dir = 'NORTH'

            if step_dir != current_dir:
                turns = self.get_required_turns(current_dir, step_dir)
                for turn in turns:
                    self.path.append((current_x, current_y, turn))
                    current_dir = turn

            if (step_x, step_y) != (current_x, current_y):
                self.path.append((step_x, step_y, current_dir))
                visited.add((step_x, step_y))
                current_x, current_y = step_x, step_y

    def find_nearest_unvisited(self, x, y, visited):
        queue = deque([(x, y)])
        seen = set()

        while queue:
            cx, cy = queue.popleft()
            if (cx, cy) in seen:
                continue
            seen.add((cx, cy))

            if (cx, cy) not in visited:
                return (cx, cy)

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    wall_key = ((cx, cy), (nx, ny)) if (cx, cy) < (nx, ny) else ((nx, ny), (cx, cy))
                    if not self.known_walls.get(wall_key, False) and (nx, ny) not in seen:
                        queue.append((nx, ny))

        return None

    def a_star(self, start, target, visited):
        start_x, start_y = start
        target_x, target_y = target

        def heuristic(x1, y1):
            return abs(x1 - target_x) + abs(y1 - target_y)

        heap = []
        heapq.heappush(heap, (0 + heuristic(start_x, start_y), 0, start_x, start_y, []))
        seen = set()

        while heap:
            _, cost, x, y, path = heapq.heappop(heap)

            if (x, y) == (target_x, target_y):
                return path + [(x, y)]

            if (x, y) in seen:
                continue
            seen.add((x, y))

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    wall_key = ((x, y), (nx, ny)) if (x, y) < (nx, ny) else ((nx, ny), (x, y))
                    if not self.known_walls.get(wall_key, False):
                        heapq.heappush(
                            heap,
                            (cost + 1 + heuristic(nx, ny), cost + 1, nx, ny, path + [(nx, ny)])
                        )
        return None

    def get_required_turns(self, current_dir, target_dir):
        current_idx = self.directions.index(current_dir)
        target_idx = self.directions.index(target_dir)
        diff = (target_idx - current_idx) % 4
        if diff == 0:
            return []
        elif diff == 1:
            return [self.directions[(current_idx + 1) % 4]]
        elif diff == 3:
            return [self.directions[(current_idx - 1) % 4]]
        elif diff == 2:
            return [self.directions[(current_idx + 1) % 4], self.directions[(current_idx + 2) % 4]]
        return []

    def get_next_step(self):
        if not self.scanned_cells:
            self.scan_environment(self.current_pos)

        if not self.scanned_cells:
            return None

        if self.path_index >= len(self.path) or not self.path:
            self.initialize_path()
            self.path_index = 0
            if not self.path:
                return None

        x, y, direction = self.path[self.path_index]
        self.path_index += 1

        wall_key = ((self.current_pos[0], self.current_pos[1]), (x, y)) if (self.current_pos[0], self.current_pos[1]) < (x, y) else ((x, y), (self.current_pos[0], self.current_pos[1]))
        if self.walls.get(wall_key, False):
            self.initialize_path()
            self.path_index = 0
            return self.get_next_step()

        if (x, y) != self.current_pos:
            target_dir = direction
            if x > self.current_pos[0]:
                target_dir = 'EAST'
            elif x < self.current_pos[0]:
                target_dir = 'WEST'
            elif y > self.current_pos[1]:
                target_dir = 'SOUTH'
            elif y < self.current_pos[1]:
                target_dir = 'NORTH'
            if target_dir != self.current_dir:
                turns = self.get_required_turns(self.current_dir, target_dir)
                if turns:
                    self.current_dir = turns[0]
                    self.path_index -= 1
                    return (self.current_pos[0], self.current_pos[1], self.current_dir)
            self.current_pos = (x, y)
            self.visited[(x, y)] = self.visited.get((x, y), 0) + 1
            self.scanned_cells.discard((x, y))
            self.scan_environment((x, y))
        return (x, y, self.current_dir)