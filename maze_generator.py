import random

class MazeGenerator:
    def __init__(self, rows, cols, density=0.3):
        self.rows = rows
        self.cols = cols
        self.density = min(max(density, 0.05), 0.95)
        self.walls = {}
        self.parent = {}
        self.rank = {}

    def find(self, cell):
        if self.parent[cell] != cell:
            self.parent[cell] = self.find(self.parent[cell])
        return self.parent[cell]

    def union(self, cell1, cell2):
        root1 = self.find(cell1)
        root2 = self.find(cell2)
        if root1 != root2:
            if self.rank[root1] < self.rank[root2]:
                root1, root2 = root2, root1
            self.parent[root2] = root1
            if self.rank[root1] == self.rank[root2]:
                self.rank[root1] += 1

    def generate_maze_kruskal(self):
        for y in range(self.rows):
            for x in range(self.cols):
                cell = (x, y)
                self.parent[cell] = cell
                self.rank[cell] = 0

        edges = []
        for y in range(self.rows):
            for x in range(self.cols):
                if x < self.cols - 1:
                    edges.append(((x, y), (x+1, y)))
                if y < self.rows - 1:
                    edges.append(((x, y), (x, y+1)))

        random.shuffle(edges)

        for edge in edges:
            cell1, cell2 = edge
            if self.find(cell1) != self.find(cell2):
                self.walls[edge] = False
                self.union(cell1, cell2)
            else:
                self.walls[edge] = True if random.random() < self.density else False

        for y in range(self.rows):
            for x in range(self.cols):
                if x < self.cols - 1 and ((x, y), (x+1, y)) not in self.walls:
                    self.walls[((x, y), (x+1, y))] = True if random.random() < self.density else False
                if y < self.rows - 1 and ((x, y), (x, y+1)) not in self.walls:
                    self.walls[((x, y), (x, y+1))] = True if random.random() < self.density else False

    def get_walls(self):
        return self.walls