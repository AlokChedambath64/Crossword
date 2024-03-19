import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        '''
        for words in self.words:
            if self.length != len(words):
                self.domains[self].remove(words)
        '''
        for var in self.domains:
            copydomain = self.domains[var].copy()
            for val in copydomain:
                if len(val) != var.length:
                    self.domains[var].remove(val)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        revised = False

        overlap = self.crossword.overlaps[x, y]
        if overlap is not None:
            i = overlap[0]
            j = overlap[1]

            # Create a copy of the domain of x
            copy_domain_x = self.domains[x].copy()
            
            # Iterate over the copy of the domain of x
            for val0 in copy_domain_x:
                check = False
                for val1 in self.domains[y]:
                    if val0[i] == val1[j]:
                        check = True
                        break
                if not check:
                    # Modify the original domain of x
                    self.domains[x].remove(val0)
                    revised = True
        return revised

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.

        queue = all arcs in csp
            while queue non-empty:
                (X, Y) = Dequeue(queue)
                if Revise(csp, X, Y):
                    if size of X.domain == 0:
                        return false
                    for each Z in X.neighbors - {Y}:
                            Enqueue(queue, (Z,X))
            return true
        """
        if arcs == None:
            queue = []
            for x in self.domains.keys():
                for y in self.domains.keys():
                    if x != y:
                        queue.append((x,y))
        
        if arcs != None:
            queue = []
            for arc in arcs:
                queue.append(arc)
        
        while queue:
            (x, y) = queue.pop(0)
            if self.revise(x, y):
                if len(self.domains[x]) == 0:
                    return False
                for z in self.crossword.neighbors(x):
                    if z != y:
                        queue.append((z,x))

        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for var in self.domains:
            if var not in assignment.keys():
                return False
        return True

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        vals = set()
        for key, val in assignment.items():
            if val in vals:
                return False
            else:
                vals.add(val)
            
            if len(key) != len(val):
                return False
            
            neighbors = self.crossword.neighbours(key)

            for var in neighbors:
                i, j = self.crossword.overlaps[key, var]
                if val[i] != assignment[var][j]:
                    return False

        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        values = {}
        variables = self.domains[var]
        neighbors = self.crossword.neighbors(var)
        for variable in variables:
            if variable in assignment:
                continue
            else:
                count = 0
                for neighbor in neighbors:
                    #i, j = self.crossword.overlaps(neighbor, var)
                    overlap = self.crossword.overlaps[(neighbor, var)]  
                    i, j = overlap[0], overlap[1]
                    for word in self.domains[neighbor]:
                        if word[i] == variable[j]:
                            count = count + 1
                values[variable] = count  

        #return sorted(values, key=lambda key: values[key])
        return [k for k, v in sorted(values.items(), key=lambda item: item[1])]
    


    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        possible = []
        for x in self.domains.keys():
            if x not in assignment:
                val = len(self.domains[x])
                neigh = len(self.crossword.neighbors(x))
                possible.append((x, val, neigh))
        
        possible.sort(key=lambda x: (x[1], -x[2]))
        return possible[0][0]

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        if assignment complete:
            return assignment
        var = Select-Unassigned-Var(assignment, csp)
        for value in Domain-Values(var, assignment, csp):
            if value consistent with assignment:
                add {var = value} to assignment
                result = Backtrack(assignment, csp)
                if result ≠ failure:
                    return result
                remove {var = value} from assignment
        return failure
        """
        if self.assignment_complete(assignment):
            return assignment
        var = self.select_unassigned_variable(assignment)
        for value in self.order_domain_values(var, assignment):
            assignment[var] = value
            result = self.backtrack(assignment)
            if result != None:
                return result
            assignment.pop(var)

        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
