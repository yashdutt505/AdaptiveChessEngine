"""
history.py

History stack used by the search.

Every call to make_move() pushes one UndoState.

Every call to unmake_move() restores the last UndoState.

The history owns previous irreversible state.

It does NOT own the board itself.
"""

from .undo import UndoState
class History:

    """
    Stack of UndoState objects.
    """

    def __init__(self):

        self.clear()
        # =====================================================
    # Reset
    # =====================================================

    def clear(self):

        self.stack = []
        # =====================================================
    # Push
    # =====================================================

    def push(self, undo: UndoState):

        self.stack.append(undo)
        # =====================================================
    # Pop
    # =====================================================

    def pop(self) -> UndoState:

        if not self.stack:

            raise IndexError(
                "History stack is empty."
            )

        return self.stack.pop()
        # =====================================================
    # Peek
    # =====================================================

    def peek(self):

        if not self.stack:

            return None

        return self.stack[-1]
        # =====================================================
    # Size
    # =====================================================

    def __len__(self):

        return len(self.stack)
        # =====================================================
    # Empty
    # =====================================================

    def empty(self):

        return len(self.stack) == 0
        # =====================================================
    # Debug
    # =====================================================

    def __str__(self):

        return f"History(size={len(self.stack)})"
    
    def last(self):
        """
        Returns the last UndoState without removing it.
        """

        return self.peek()
    