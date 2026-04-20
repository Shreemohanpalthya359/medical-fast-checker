import matplotlib.pyplot as plt
import numpy as np

# Data for the table
columns = ['Rank', 'Retrieved Source', 'Vector Score', 'Final Confidence']
cell_text = [
    ['1', 'NIH Clinical Guidelines', '0.96', '0.94'],
    ['2', 'PubMed Abstract #34091', '0.88', '0.85'],
    ['3', 'ChromaDB Local Entry', '0.84', '0.81'],
    ['4', 'Mayo Clinic Fact Sheet', '0.79', '0.76'],
    ['5', 'Unverified Web Article', '0.45', '0.23']
]

# Create figure and axis
fig, ax = plt.subplots(figsize=(8, 3.5))

# Hide axes
ax.axis('off')
ax.axis('tight')

# Add title (simulating LaTeX caption)
plt.title(r'$\bf{Table\ 5.1:}$ Sample RAG Retrieval Output', fontsize=16, pad=20)

# Create table
table = ax.table(cellText=cell_text,
                 colLabels=columns,
                 cellLoc='center',
                 loc='center')

# Style the table
table.auto_set_font_size(False)
table.set_fontsize(14)
table.scale(1, 2)

# Apply specific styling to match the user's example
# The user's example had vertical lines and horizontal lines at top, bottom, and header
for (row, col), cell in table.get_celld().items():
    if row == 0:
        # Header row
        cell.set_text_props(weight='normal', size=15)
        # In the user image, header has a top border and bottom border
        # matplotlib tables have borders around all cells by default
        
    # We can keep the default box borders because the user's image actually 
    # has vertical lines and horizontal lines for the table grid.
    # Wait, the user's image has a border around EVERY cell.
    cell.set_edgecolor('black')

plt.tight_layout()
plt.savefig('assets/report_retrieval_table.png', dpi=300, bbox_inches='tight')
print("Saved assets/report_retrieval_table.png")
plt.close()
