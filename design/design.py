from graphviz import Digraph

# Create a new directed graph
dot = Digraph()

# Set graph attributes (background color)
dot.attr(bgcolor="black")

# Set global node attributes (text color, fill color)
dot.attr(
    "node",
    fontcolor="lightgrey",
    color="lightgrey",
    fillcolor="darkblue",
    style="filled",
)

# Set global edge attributes (line color, label text color)
dot.attr("edge", color="lightgrey", fontcolor="lightgrey")

# Add nodes
dot.node("scraper/companies.py")
dot.node("scraper/main.py")
dot.node("Scraper")
dot.node("SQLite Database", shape="box")

# Add edges
dot.edge("scraper/companies.py", "Scraper", label="run first")
dot.edge("scraper/main.py", "Scraper", label="run second")
dot.edge("Scraper", "SQLite Database", label="updates")

# Save the source to a file
dot.save("design/design.dot")
