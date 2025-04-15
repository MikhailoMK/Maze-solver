import random
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
        self.dead_ends = set()
        self.path_history = []
        self.update_known_walls(start_pos)

    def update_known_walls(self, pos):
        x, y = pos
        for dx, dy, direction in [(-1, 0, 'WEST'), (1, 0, 'EAST'), (0, -1, 'NORTH'), (0, 1, 'SOUTH')]:
            nx, ny = x + dx, y + dy
            wall_key = ((x, y), (nx, ny)) if (x, y) < (nx, ny) else ((nx, ny), (x, y))
            if nx < 0 or nx >= self.cols or ny < 0 or ny >= self.rows:
                self.known_walls[wall_key] = True
            else:
                self.known_walls[wall_key] = self.walls.get(wall_key, False)

    def get_wall_count(self, x, y):
        wall_count = 0
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            wall_key = ((x, y), (nx, ny)) if (x, y) < (nx, ny) else ((nx, ny), (x, y))
            if nx < 0 or nx >= self.cols or ny < 0 or ny >= self.rows:
                wall_count += 1
            elif wall_key in self.known_walls and self.known_walls[wall_key]:
                wall_count += 1
        return wall_count

    def get_next_step(self):
        x, y = self.current_pos
        self.update_known_walls((x, y))

        neighbors = []
        unvisited_neighbors = []
        for dx, dy, direction in [(-1, 0, 'WEST'), (1, 0, 'EAST'), (0, -1, 'NORTH'), (0, 1, 'SOUTH')]:
            nx, ny = x + dx, y + dy
            if nx < 0 or nx >= self.cols or ny < 0 or ny >= self.rows:
                continue
            wall_key = ((x, y), (nx, ny)) if (x, y) < (nx, ny) else ((nx, ny), (x, y))
            if self.known_walls.get(wall_key, False):
                continue
            neighbors.append((nx, ny, direction))
            visits = self.visited.get((nx, ny), 0)
            max_visits = 4 - self.get_wall_count(nx, ny)
            if visits == 0 and visits < max_visits and (nx, ny) not in self.dead_ends:
                unvisited_neighbors.append((nx, ny, direction))

        if unvisited_neighbors:
            nx, ny, direction = random.choice(unvisited_neighbors)
            self.path_history.append(self.current_pos)
            self.current_pos = (nx, ny)
            self.current_dir = direction
            return (nx, ny, direction)

        all_neighbors_full = True
        for nx, ny, _ in neighbors:
            visits = self.visited.get((nx, ny), 0)
            max_visits = 4 - self.get_wall_count(nx, ny)
            if visits < max_visits and (nx, ny) not in self.dead_ends:
                all_neighbors_full = False
                break

        if all_neighbors_full and neighbors and (x, y) != self.start_pos:
            self.dead_ends.add((x, y))

        if not unvisited_neighbors and neighbors:
            target = self.find_nearest_unvisited()
            if target:
                path = self.astar_path(target)
                if path:
                    nx, ny = path[0]
                    if nx > x:
                        direction = 'EAST'
                    elif nx < x:
                        direction = 'WEST'
                    elif ny > y:
                        direction = 'SOUTH'
                    else:
                        direction = 'NORTH'
                    self.path_history.append(self.current_pos)
                    self.current_pos = (nx, ny)
                    self.current_dir = direction
                    return (nx, ny, direction)
                else:
                    seen = set()
                    queue = deque([((x, y), [])])
                    while queue:
                        (cx, cy), path = queue.popleft()
                        if (cx, cy) in seen:
                            continue
                        seen.add((cx, cy))
                        self.dead_ends.add((cx, cy))
                        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            nx, ny = cx + dx, cy + dy
                            if nx < 0 or nx >= self.cols or ny < 0 or ny >= self.rows:
                                continue
                            wall_key = ((cx, cy), (nx, ny)) if (cx, cy) < (nx, ny) else ((nx, ny), (cx, cy))
                            if self.known_walls.get(wall_key, False):
                                continue
                            visits = self.visited.get((nx, ny), 0)
                            max_visits = 4 - self.get_wall_count(nx, ny)
                            if visits == 0 and visits < max_visits:
                                path_to_unvisited = self.astar_path((nx, ny))
                                if path_to_unvisited:
                                    nx, ny = path_to_unvisited[0]
                                    if nx > x:
                                        direction = 'EAST'
                                    elif nx < x:
                                        direction = 'WEST'
                                    elif ny > y:
                                        direction = 'SOUTH'
                                    else:
                                        direction = 'NORTH'
                                    self.path_history.append(self.current_pos)
                                    self.current_pos = (nx, ny)
                                    self.current_dir = direction
                                    return (nx, ny, direction)
                            queue.append(((nx, ny), path + [(nx, ny)]))
                    while self.path_history:
                        prev_pos = self.path_history.pop()
                        path = self.astar_path(prev_pos)
                        if path:
                            nx, ny = path[0]
                            if nx > x:
                                direction = 'EAST'
                            elif nx < x:
                                direction = 'WEST'
                            elif ny > y:
                                direction = 'SOUTH'
                            else:
                                direction = 'NORTH'
                            self.current_pos = (nx, ny)
                            self.current_dir = direction
                            return (nx, ny, direction)
                    return None

        if self.all_cells_visited():
            path = self.astar_path(self.start_pos)
            if path:
                nx, ny = path[0]
                if nx > x:
                    direction = 'EAST'
                elif nx < x:
                    direction = 'WEST'
                elif ny > y:
                    direction = 'SOUTH'
                else:
                    direction = 'NORTH'
                self.current_pos = (nx, ny)
                self.current_dir = direction
                return (nx, ny, direction)

        return None

    def find_nearest_unvisited(self):
        x, y = self.current_pos
        queue = deque([(x, y, 0)])
        seen = set([(x, y)])
        candidates = []

        while queue:
            cx, cy, distance = queue.popleft()
            
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = cx + dx, cy + dy
                if nx < 0 or nx >= self.cols or ny < 0 or ny >= self.rows:
                    continue
                wall_key = ((cx, cy), (nx, ny)) if (cx, cy) < (nx, ny) else ((nx, ny), (cx, cy))
                if self.known_walls.get(wall_key, False):
                    continue
                if (nx, ny) in seen:
                    continue
                
                visits = self.visited.get((nx, ny), 0)
                max_visits = 4 - self.get_wall_count(nx, ny)
                
                if visits == 0 and visits < max_visits and (nx, ny) not in self.dead_ends:
                    candidates.append((distance + 1, nx, ny))
                seen.add((nx, ny))
                queue.append((nx, ny, distance + 1))
        
        if not candidates:
            return None
        
        min_distance = min(d for d, _, _ in candidates)
        closest_candidates = [(d, nx, ny) for d, nx, ny in candidates if d == min_distance]
        
        sx, sy = self.start_pos
        max_start_distance = -1
        best_candidate = None
        
        for _, nx, ny in closest_candidates:
            start_distance = abs(nx - sx) + abs(ny - sy)
            if start_distance > max_start_distance:
                max_start_distance = start_distance
                best_candidate = (nx, ny)
        
        return best_candidate

    def astar_path(self, target):
        if not target:
            return None
        
        x, y = self.current_pos
        tx, ty = target
        open_set = [(0, x, y, [])]
        closed_set = set()
        g_score = {(x, y): 0}
        
        while open_set:
            open_set.sort()
            f, cx, cy, path = open_set.pop(0)
            
            if (cx, cy) == (tx, ty):
                return path
            
            if (cx, cy) in closed_set:
                continue
            
            closed_set.add((cx, cy))
            
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = cx + dx, cy + dy
                if nx < 0 or nx >= self.cols or ny < 0 or ny >= self.rows:
                    continue
                wall_key = ((cx, cy), (nx, ny)) if (cx, cy) < (nx, ny) else ((nx, ny), (cx, cy))
                if self.known_walls.get(wall_key, False):
                    continue
                if (nx, ny) in closed_set:
                    continue
                
                new_g = g_score[(cx, cy)] + 1
                h = abs(nx - tx) + abs(ny - ty)
                f = new_g + h
                
                if (nx, ny) not in g_score or new_g < g_score[(nx, ny)]:
                    g_score[(nx, ny)] = new_g
                    open_set.append((f, nx, ny, path + [(nx, ny)]))
        
        return None

    def all_cells_visited(self):
        for y in range(self.rows):
            for x in range(self.cols):
                if (x, y) not in self.visited or self.visited[(x, y)] == 0:
                    return False
        return True

    def get_required_turns(self, current_dir, target_dir):
        turns = []
        current_idx = self.directions.index(current_dir)
        target_idx = self.directions.index(target_dir)
        
        if (target_idx - current_idx) % 4 == 1:
            turns.append(self.directions[(current_idx + 1) % 4])
        elif (target_idx - current_idx) % 4 == 3:
            turns.append(self.directions[(current_idx - 1) % 4])
        elif abs(target_idx - current_idx) == 2:
            turns.append(self.directions[(current_idx + 1) % 4])
            turns.append(self.directions[(current_idx + 2) % 4])
        
        return turns