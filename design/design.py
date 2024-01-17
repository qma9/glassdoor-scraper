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
dot.node("API Post Endpoints", shape="box")
dot.node("companies/")
dot.node("glassdoor/")
dot.node("Scraper")
dot.node("MySQL Database")

# Add edges
dot.edge("API Post Endpoints", "companies/", label="run first")
dot.edge("API Post Endpoints", "glassdoor/", label="run second")
dot.edge("companies/", "Scraper", label="triggers")
dot.edge("glassdoor/", "Scraper", label="triggers")
dot.edge("Scraper", "MySQL Database", label="updates")

# Save the source to a file
dot.save("design/design.dot")
