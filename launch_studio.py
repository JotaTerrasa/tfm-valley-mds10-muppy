from graph_studio_simulado import build_graph

if __name__ == "__main__":
    grafo = build_graph()
  
    import langgraph
    langgraph.graph_studio.run(grafo)  