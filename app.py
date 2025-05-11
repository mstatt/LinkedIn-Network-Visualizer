import streamlit as st
import streamlit.components.v1 as components
import networkx as nx
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime
import random
from io import StringIO

# Set page configuration
st.set_page_config(page_title="LinkedIn Social Graph Visualizer", layout="wide")

# Add Bootstrap CSS
st.markdown("""
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
    .person-card {
        margin: 20px 0;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        background-color: white;
        border: 1px solid #e0e0e0;
        color: #0077b5;
    }
    .card-header {
        background-color: #0077b5;
        color: white;
        border-radius: 8px 8px 0 0;
        padding: 15px;
        margin: -20px -20px 20px -20px;
    }
    .main-card {
        background-color: #f0f8ff;
        border: 2px solid #0077b5;
        color: #0077b5;
    }
    .connection-card {
        background-color: #f8f9fa;
        border: 1px solid #4a90e2;
        color: #0077b5;
    }
    .badge {
        background-color: #0077b5;
        color: white;
        padding: 5px 10px;
        border-radius: 12px;
        font-size: 12px;
    }
    .company-badge {
        background-color: #4a90e2;
        color: white;
        padding: 3px 8px;
        border-radius: 8px;
        font-size: 11px;
        margin-left: 10px;
    }
    .upload-section {
        background-color: #f8f9fa;
        border: 2px solid #0077b5;
        border-radius: 8px;
        padding: 40px;
        text-align: center;
        margin: 20px 0;
    }
    .stats-card {
        text-align: center;
        padding: 20px;
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px;
    }
    h1, h2, h3, h4, h5, h6, p, span, label, .stTextInput label, .stSelectbox label {
        color: #0077b5 !important;
    }
    .info-text {
        color: #666;
        font-size: 14px;
        line-height: 1.6;
    }
    .url-link {
        color: #0077b5;
        text-decoration: underline;
        word-break: break-all;
    }
    .timeline-section {
        margin-top: 40px;
        padding: 20px;
        background-color: #f8f9fa;
        border-radius: 8px;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        border-radius: 8px;
        padding: 15px;
        margin: 20px 0;
        color: #856404;
    }
    .example-format {
        background-color: #f5f5f5;
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 15px;
        margin: 10px 0;
        font-family: monospace;
        font-size: 12px;
        white-space: pre-wrap;
        overflow-x: auto;
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.title("LinkedIn Network Visualizer")
st.write("Upload your LinkedIn Connections.csv file to visualize your professional network.")

# Initialize session state
if 'selected_node' not in st.session_state:
    st.session_state.selected_node = None
if 'graph_data' not in st.session_state:
    st.session_state.graph_data = None

# File upload section
st.markdown("""
<div class="upload-section">
    <h3 style="color: #0077b5; margin-bottom: 20px;">Upload Your LinkedIn Data</h3>
    <p class="info-text">Download your LinkedIn data archive and upload the Connections.csv file.</p>
    <p class="info-text">To download your data: LinkedIn Settings → Privacy → Get a copy of your data → Request archive</p>
</div>
""", unsafe_allow_html=True)

# Add note about email addresses
st.markdown("""
<div class="warning-box">
    <h5 style="color: #856404;">📧 Note about Email Addresses</h5>
    <p>Some email addresses may be missing from your connections CSV. You will only see email addresses for connections who have allowed their connections to see or download their email address.</p>
    <p>Learn more: <a href="https://www.linkedin.com/help/linkedin/answer/261" target="_blank">LinkedIn Help on Email Privacy</a></p>
</div>
""", unsafe_allow_html=True)


uploaded_file = st.file_uploader("Choose your Connections.csv file", type=['csv'], help="Upload the Connections.csv file from your LinkedIn data download")

if uploaded_file is not None:
    try:
        # Read the CSV file - handle potential encoding issues and special characters
        df = None
        
        # Try reading with UTF-8 encoding first
        try:
            uploaded_file.seek(0)
            content = uploaded_file.read().decode('utf-8')
            lines = content.split('\n')
            
            # Find the header line (first line that starts with "First Name")
            header_index = 0
            for i, line in enumerate(lines):
                if line.startswith('First Name'):
                    header_index = i
                    break
            
            # Skip to the header and process the CSV
            csv_content = '\n'.join(lines[header_index:])
            csv_file = StringIO(csv_content)
            
            # Read with specific parameters to handle LinkedIn's format
            df = pd.read_csv(csv_file, 
                           encoding='utf-8',
                           quotechar='"',
                           escapechar='\\',
                           doublequote=True,
                           skipinitialspace=True)
        except Exception as e1:
            # Try with Latin-1 encoding
            try:
                uploaded_file.seek(0)
                content = uploaded_file.read().decode('latin-1')
                lines = content.split('\n')
                
                # Find the header line
                header_index = 0
                for i, line in enumerate(lines):
                    if line.startswith('First Name'):
                        header_index = i
                        break
                
                csv_content = '\n'.join(lines[header_index:])
                csv_file = StringIO(csv_content)
                
                df = pd.read_csv(csv_file, 
                               encoding='latin-1',
                               quotechar='"',
                               escapechar='\\',
                               doublequote=True,
                               skipinitialspace=True)
            except Exception as e2:
                # Last resort: try with different parameters
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, 
                               encoding='utf-8',
                               sep=',',
                               quotechar='"',
                               on_bad_lines='skip')
        
        # Clean column names - LinkedIn files might have leading/trailing spaces
        df.columns = df.columns.str.strip()
        
        # Expected columns
        expected_columns = ['First Name', 'Last Name', 'URL', 'Email Address', 'Company', 'Position', 'Connected On']
        
        # Verify columns
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            st.error(f"Missing columns in CSV: {', '.join(missing_columns)}")
            st.info("Expected columns: " + ", ".join(expected_columns))
            st.info("Found columns: " + ", ".join(df.columns.tolist()))
            
            # Show first few lines to help debug
            st.markdown("**First few lines of your file:**")
            uploaded_file.seek(0)
            content = uploaded_file.read().decode('utf-8', errors='replace')
            st.text(content[:500])
        else:
            # Display file info
            st.success(f"Successfully loaded {len(df)} connections!")
            
            # Create a preview of the data
            with st.expander("Preview your connections data"):
                # Show sample data with sensitive info masked
                preview_df = df.head(10).copy()
                if 'Email Address' in preview_df.columns:
                    preview_df['Email Address'] = preview_df['Email Address'].apply(
                        lambda x: ('***' + x.split('@')[1]) if pd.notna(x) and '@' in str(x) else ''
                    )
                st.dataframe(preview_df)
                
                # Show column information
                st.markdown("### CSV Columns summary:")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"- **Total Connections**: {len(df)}")
                    st.markdown(f"- **With Email**: {len(df[df['Email Address'].notna()])}")
                    st.markdown(f"- **With Company**: {len(df[df['Company'].notna()])}")
                with col2:
                    st.markdown(f"- **With Position**: {len(df[df['Position'].notna()])}")
                    st.markdown(f"- **With URL**: {len(df[df['URL'].notna()])}")
                    st.markdown(f"- **With Connected Date**: {len(df[df['Connected On'].notna()])}")
            
            # Process the data
            connections = []
            
            # Create main person data (the user)
            main_person_data = {
                "name": "You",
                "type": "main",
                "title": "Your Title",
                "company": "Your Company",
                "location": "Your Location",
                "email": "your.email@company.com",
                "experience": "Your experience",
                "education": "Your education",
                "skills": ["Your", "Skills"],
                "connected_on": None,
                "url": None
            }
            
            # Process each connection
            for idx, row in df.iterrows():
                # Extract data from CSV columns
                first_name = str(row['First Name']).strip() if pd.notna(row['First Name']) else ""
                last_name = str(row['Last Name']).strip() if pd.notna(row['Last Name']) else ""
                url = str(row['URL']).strip() if pd.notna(row['URL']) else ""
                email = str(row['Email Address']).strip() if pd.notna(row['Email Address']) else ""
                company = str(row['Company']).strip() if pd.notna(row['Company']) else "Unknown Company"
                position = str(row['Position']).strip() if pd.notna(row['Position']) else "Professional"
                connected_on = str(row['Connected On']).strip() if pd.notna(row['Connected On']) else ""
                
                # Skip empty names
                if not first_name and not last_name:
                    continue
                
                # Create full name
                full_name = f"{first_name} {last_name}".strip()
                
                # Convert Connected On to standard format
                connected_date_formatted = ""
                if connected_on:
                    try:
                        # Parse LinkedIn's format "27 Aug 2010"
                        date_obj = datetime.strptime(connected_on, '%d %b %Y')
                        connected_date_formatted = date_obj.strftime('%B %d, %Y')
                    except ValueError:
                        # If parsing fails, keep original
                        connected_date_formatted = connected_on
                
                # Create connection data
                connection_data = {
                    "name": full_name,
                    "type": "connection",
                    "title": position,
                    "company": company,
                    "location": "Location not available",
                    "email": email,
                    "experience": f"Works at {company}",
                    "education": "Education not available",
                    "skills": ["Professional Networking"],
                    "connected_on": connected_date_formatted,
                    "url": url,
                    "raw_connected_on": connected_on  # Keep raw format for sorting
                }
                connections.append(connection_data)
            
            # Create the network graph
            G = nx.Graph()
            
            # Add the main person
            G.add_node("You", **main_person_data)
            
            # Add connections and edges
            for connection in connections:
                # Ensure unique node names
                node_name = connection['name']
                counter = 1
                original_name = node_name
                while node_name in G.nodes():
                    node_name = f"{original_name} ({counter})"
                    counter += 1
                
                connection['name'] = node_name
                G.add_node(node_name, **connection)
                G.add_edge("You", node_name)
            
            # Store graph data in session state
            st.session_state.graph_data = G
            
            # Create the visualization
            st.subheader(f"Your LinkedIn Network - {len(connections)} Connections")
            
            # Add visualization controls
            col1, col2, col3 = st.columns(3)
            
            with col1:
                layout_algorithm = st.selectbox(
                    "Layout Algorithm",
                    ["Spring Layout", "Circular Layout", "Random Layout", "Kamada Kawai"],
                    help="Choose how connections are arranged in the graph"
                )
            
            with col2:
                sample_size = st.slider(
                    "Number of Connections to Show",
                    min_value=min(50, len(connections)),
                    max_value=min(len(connections), 1000),
                    value=min(len(connections), 300),
                    help="Adjust to reduce clutter in large networks"
                )
            
            with col3:
                visualization_mode = st.selectbox(
                    "Visualization Mode",
                    ["All Connections", "Company Clusters", "Most Connected"],
                    help="Choose how to group and display connections"
                )
            
            # Additional controls
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                show_labels = st.checkbox("Show name labels", value=True)
            
            with col2:
                show_edges = st.checkbox("Show connection lines", value=True)
            
            with col3:
                node_spacing = st.slider("Node Spacing", 1.0, 5.0, 2.5, 0.5)
            
            with col4:
                color_by = st.selectbox("Color nodes by", ["Type", "Company", "Connection Date"])
            
            # Create sidebar with search and filter functionality BEFORE using selected_company
            st.sidebar.header("Network Explorer")
            
            # Search functionality
            search_query = st.sidebar.text_input("Search connections:", placeholder="Enter name...")
            if search_query:
                matching_nodes = [node for node in G.nodes() if search_query.lower() in node.lower()]
                if matching_nodes:
                    st.sidebar.subheader("Search Results")
                    for node in matching_nodes[:10]:  # Limit to first 10 results
                        if st.sidebar.button(f"View {node}", key=f"search_{node}"):
                            st.session_state.selected_node = node
                            st.rerun()
                    if len(matching_nodes) > 10:
                        st.sidebar.text(f"... and {len(matching_nodes) - 10} more")
            
            # Advanced Filters
            st.sidebar.subheader("Advanced Filters")
            
            # Filter by company
            all_companies = sorted(list(set([c['company'] for c in connections if c['company'] != "Unknown Company"])))
            selected_company = st.sidebar.selectbox("Filter by Company:", ["All"] + all_companies[:50])  # Show top 50 companies
            
            # Filter by connection date
            st.sidebar.markdown("**Connection Date Range**")
            connections_with_dates = [c for c in connections if c['raw_connected_on']]
            
            if connections_with_dates:
                try:
                    dates = []
                    for conn in connections_with_dates:
                        try:
                            date = datetime.strptime(conn['raw_connected_on'], '%d %b %Y')
                            dates.append(date)
                        except:
                            continue
                    
                    if dates:
                        min_date = min(dates)
                        max_date = max(dates)
                        
                        selected_date_range = st.sidebar.date_input(
                            "Connection Date Range",
                            value=(min_date, max_date),
                            min_value=min_date,
                            max_value=max_date
                        )
                except:
                    pass
            
            # Filter by email availability
            email_filter = st.sidebar.selectbox(
                "Email Filter",
                ["All", "With Email", "Without Email"]
            )
            
            # Quick filters for common companies
            if all_companies:
                top_companies = pd.Series([c['company'] for c in connections if c['company'] != "Unknown Company"]).value_counts().head(5)
                st.sidebar.subheader("Quick Filters - Top Companies")
                for company, count in top_companies.items():
                    if st.sidebar.button(f"{company} ({count})", key=f"quick_{company}"):
                        selected_company = company
                        st.rerun()
            
            # Apply filters
            filtered_nodes = []
            if selected_company != "All":
                filtered_nodes = [node for node in G.nodes() if G.nodes[node].get('company') == selected_company and node != "You"]
                st.sidebar.subheader(f"People at {selected_company}")
                for node in filtered_nodes[:10]:  # Show first 10
                    if st.sidebar.button(f"View {node}", key=f"company_{node}"):
                        st.session_state.selected_node = node
                        st.rerun()
                if len(filtered_nodes) > 10:
                    st.sidebar.text(f"... and {len(filtered_nodes) - 10} more")
            
            # Network insights
            st.sidebar.subheader("Network Insights")
            st.sidebar.metric("Total Connections", len(connections))
            st.sidebar.metric("Companies", len(all_companies))
            avg_connections_per_company = round(len(connections) / len(all_companies), 1) if all_companies else 0
            st.sidebar.metric("Avg per Company", avg_connections_per_company)
            
            # Handle different visualization modes
            sampled_connections = []
            
            if visualization_mode == "Company Clusters":
                # Group by top companies
                company_counts = pd.Series([c['company'] for c in connections if c['company'] != "Unknown Company"]).value_counts()
                top_companies = company_counts.head(10).index.tolist()
                
                # Add connections from top companies
                for company in top_companies:
                    company_connections = [c for c in connections if c['company'] == company]
                    # Limit connections per company to avoid overcrowding
                    max_per_company = max(sample_size // 10, 5)
                    sampled_connections.extend(company_connections[:max_per_company])
                
                # Fill remaining slots with other connections
                remaining = sample_size - len(sampled_connections)
                if remaining > 0:
                    other_connections = [c for c in connections if c['company'] not in top_companies]
                    sampled_connections.extend(other_connections[:remaining])
            
            elif visualization_mode == "Most Connected":
                # Prioritize people with common titles or companies
                title_counts = pd.Series([c['title'] for c in connections]).value_counts()
                common_titles = title_counts.head(20).index.tolist()
                
                # Add connections with common titles first
                priority_connections = [c for c in connections if c['title'] in common_titles]
                remaining_connections = [c for c in connections if c['title'] not in common_titles]
                
                if len(priority_connections) > sample_size:
                    sampled_connections = random.sample(priority_connections, sample_size)
                else:
                    sampled_connections = priority_connections
                    remaining = sample_size - len(sampled_connections)
                    if remaining > 0:
                        sampled_connections.extend(random.sample(remaining_connections, remaining))
            
            else:  # All Connections mode
                # If filtering by company, prioritize those connections
                if selected_company != "All":
                    filtered_connections = [c for c in connections if c['company'] == selected_company]
                    sampled_connections = filtered_connections
                    # Add remaining connections up to sample_size
                    remaining = sample_size - len(sampled_connections)
                    if remaining > 0:
                        other_connections = [c for c in connections if c['company'] != selected_company]
                        sampled_connections.extend(other_connections[:remaining])
                else:
                    # Random sample for large networks
                    if len(connections) > sample_size:
                        sampled_connections = random.sample(connections, sample_size)
                    else:
                        sampled_connections = connections
            
            # Create a subgraph with sampled connections
            G_vis = nx.Graph()
            G_vis.add_node("You", **main_person_data)
            
            for connection in sampled_connections:
                node_name = connection['name']
                counter = 1
                original_name = node_name
                while node_name in G_vis.nodes():
                    node_name = f"{original_name} ({counter})"
                    counter += 1
                
                G_vis.add_node(node_name, **connection)
                G_vis.add_edge("You", node_name)
            
            # Choose layout algorithm
            if layout_algorithm == "Spring Layout":
                pos = nx.spring_layout(G_vis, k=node_spacing, iterations=50)
            elif layout_algorithm == "Circular Layout":
                pos = nx.circular_layout(G_vis)
            elif layout_algorithm == "Random Layout":
                pos = nx.random_layout(G_vis)
            else:  # Kamada Kawai
                pos = nx.kamada_kawai_layout(G_vis)
            
            # Create visualization
            fig_data = []
            
            # Create edge trace if enabled
            if show_edges:
                edge_x = []
                edge_y = []
                for edge in G_vis.edges():
                    x0, y0 = pos[edge[0]]
                    x1, y1 = pos[edge[1]]
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])
                
                edge_trace = go.Scatter(
                    x=edge_x, y=edge_y,
                    line=dict(width=1, color='rgba(125,125,125,0.3)'),
                    hoverinfo='none',
                    mode='lines'
                )
                fig_data.append(edge_trace)
            
            # Create node trace with color coding
            node_x = []
            node_y = []
            node_text = []
            node_color = []
            node_size = []
            hover_text = []
            
            # Define color palettes
            import plotly.express as px
            company_colors = px.colors.qualitative.Plotly
            date_colors = px.colors.sequential.Viridis
            
            # Get unique values for coloring
            if color_by == "Company":
                unique_companies = list(set([G_vis.nodes[node].get('company', 'Unknown') for node in G_vis.nodes() if node != "You"]))
                company_color_map = {company: company_colors[i % len(company_colors)] for i, company in enumerate(unique_companies)}
            elif color_by == "Connection Date":
                # Parse dates for color mapping
                date_values = {}
                for node in G_vis.nodes():
                    if node != "You":
                        raw_date = G_vis.nodes[node].get('raw_connected_on', '')
                        if raw_date:
                            try:
                                date_obj = datetime.strptime(raw_date, '%d %b %Y')
                                date_values[node] = date_obj.timestamp()
                            except:
                                date_values[node] = 0
                        else:
                            date_values[node] = 0
                
                # Normalize dates for color scale
                if date_values:
                    min_date = min(date_values.values())
                    max_date = max(date_values.values())
                    if max_date > min_date:
                        for node in date_values:
                            date_values[node] = (date_values[node] - min_date) / (max_date - min_date)
            
            for node in G_vis.nodes():
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)
                
                node_data = G_vis.nodes[node]
                if node_data['type'] == 'main':
                    node_text.append("You" if show_labels else "")
                    node_color.append('#0077b5')
                    node_size.append(40)
                else:
                    # Show first name for nodes if labels are enabled
                    node_text.append(node.split()[0] if show_labels else "")
                    
                    # Apply color coding
                    if color_by == "Company":
                        company = node_data.get('company', 'Unknown')
                        node_color.append(company_color_map.get(company, '#4a90e2'))
                    elif color_by == "Connection Date" and node in date_values:
                        # Use viridis color scale
                        color_index = int(date_values[node] * (len(date_colors) - 1))
                        node_color.append(date_colors[color_index])
                    else:
                        node_color.append('#4a90e2')
                    
                    # Adjust node size based on visualization mode
                    if visualization_mode == "Company Clusters":
                        # Make nodes from same company slightly larger
                        node_size.append(25)
                    else:
                        node_size.append(20)
                
                # Enhanced hover information
                hover_info = [
                    f"<b>{node}</b>",
                    f"Title: {node_data.get('title', 'N/A')}",
                    f"Company: {node_data.get('company', 'N/A')}",
                    f"Connected: {node_data.get('connected_on', 'N/A')}"
                ]
                hover_text.append("<br>".join(hover_info))
            
            node_trace = go.Scatter(
                x=node_x, y=node_y,
                mode='markers+text' if show_labels else 'markers',
                hoverinfo='text',
                hovertext=hover_text,
                text=node_text,
                textposition="top center",
                textfont=dict(color='#0077b5', size=12),
                marker=dict(
                    size=node_size,
                    color=node_color,
                    line=dict(width=2, color='white')
                )
            )
            fig_data.append(node_trace)
            
            # Create the figure
            fig = go.Figure(data=fig_data,
                           layout=go.Layout(
                               title=dict(
                                   text=f'Showing {len(sampled_connections)} of {len(connections)} connections - Click on any node to see details',
                                   font=dict(size=16, color='#0077b5')
                               ),
                               showlegend=False,
                               hovermode='closest',
                               margin=dict(b=40,l=20,r=20,t=60),
                               xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                               yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                               plot_bgcolor='white',
                               dragmode='pan'
                           ))
            
            # Add zoom and pan instructions
            st.info("💡 Tip: Use mouse wheel to zoom, click and drag to pan, double-click to reset view")
            
            # Display the graph
            st.plotly_chart(fig, use_container_width=True, key="network_graph")
            
            # Add legend for color coding
            if color_by == "Company" and visualization_mode == "Company Clusters":
                st.subheader("Color Legend")
                legend_cols = st.columns(min(5, len(company_color_map)))
                for i, (company, color) in enumerate(list(company_color_map.items())[:10]):
                    with legend_cols[i % 5]:
                        st.markdown(f"🔵 <span style='color: {color};'>■</span> {company}", unsafe_allow_html=True)
                if len(company_color_map) > 10:
                    st.text("... and more")
            
            # Show company distribution for current view
            st.subheader("Current View Statistics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Connections Shown", len(sampled_connections))
            
            with col2:
                companies_shown = [c['company'] for c in sampled_connections if c['company'] != "Unknown Company"]
                unique_companies_shown = len(set(companies_shown))
                st.metric("Companies Shown", unique_companies_shown)
            
            with col3:
                if selected_company != "All":
                    company_count = len([c for c in sampled_connections if c['company'] == selected_company])
                    st.metric(f"{selected_company} Connections", company_count)
            
            # Network statistics
            st.subheader("Network Statistics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="stats-card">
                    <h4 style="color: #0077b5;">Total Connections</h4>
                    <h2 style="color: #0077b5;">{len(connections)}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Count unique companies
                companies = [c['company'] for c in connections if c['company'] != "Unknown Company"]
                unique_companies = len(set(companies))
                st.markdown(f"""
                <div class="stats-card">
                    <h4 style="color: #0077b5;">Companies</h4>
                    <h2 style="color: #0077b5;">{unique_companies}</h2>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                # Count connections with email
                with_email = len([c for c in connections if c['email']])
                st.markdown(f"""
                <div class="stats-card">
                    <h4 style="color: #0077b5;">With Email</h4>
                    <h2 style="color: #0077b5;">{with_email}</h2>
                    <small style="color: #666;">({round(with_email/len(connections)*100, 1)}%)</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                # Count connections with LinkedIn URLs
                with_url = len([c for c in connections if c['url']])
                st.markdown(f"""
                <div class="stats-card">
                    <h4 style="color: #0077b5;">With LinkedIn URL</h4>
                    <h2 style="color: #0077b5;">{with_url}</h2>
                    <small style="color: #666;">({round(with_url/len(connections)*100, 1)}%)</small>
                </div>
                """, unsafe_allow_html=True)
            
            # Advanced Network Analysis
            st.subheader("Network Analysis & Insights")
            
            # Create tabs for different analyses
            tab1, tab2, tab3, tab4 = st.tabs(["Network Metrics", "Company Analysis", "Industry Clusters", "Recommendations"])
            
            with tab1:
                # Calculate network metrics
                col1, col2, col3, col4 = st.columns(4)
                
                # Network density
                density = nx.density(G)
                with col1:
                    st.metric("Network Density", f"{density:.4f}", 
                             help="How interconnected your network is (0-1 scale)")
                
                # Average degree
                avg_degree = sum(dict(G.degree()).values()) / len(G.nodes())
                with col2:
                    st.metric("Avg Connections per Person", f"{avg_degree:.1f}")
                
                # Companies per connection ratio
                unique_companies = len(set([c['company'] for c in connections if c['company'] != "Unknown Company"]))
                diversity_ratio = unique_companies / len(connections) if connections else 0
                with col3:
                    st.metric("Network Diversity", f"{diversity_ratio:.2f}", 
                             help="Ratio of unique companies to total connections")
                
                # Email availability
                email_percentage = (with_email / len(connections)) * 100 if connections else 0
                with col4:
                    st.metric("Contact Rate", f"{email_percentage:.1f}%", 
                             help="Percentage of connections with email addresses")
                
                # Network visualization insights
                st.markdown("### Network Structure Insights")
                st.markdown(f"""
                - Your network has **{len(connections)} connections** across **{unique_companies} companies**
                - The average connection has **{avg_degree:.1f}** connections in your network
                - Your network diversity score is **{diversity_ratio:.2f}** (higher = more diverse)
                - You have contact information for **{with_email}** connections ({email_percentage:.1f}%)
                """)
            
            with tab2:
                # Company Analysis
                st.markdown("### Company Distribution Analysis")
                
                # Create company analysis dataframe
                company_analysis = pd.DataFrame({
                    'Company': [c['company'] for c in connections if c['company'] != "Unknown Company"]
                })
                company_counts = company_analysis['Company'].value_counts()
                
                # Company size categories
                large_companies = company_counts[company_counts >= 10].index.tolist()
                medium_companies = company_counts[(company_counts >= 5) & (company_counts < 10)].index.tolist()
                small_companies = company_counts[company_counts < 5].index.tolist()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Large Companies (10+ connections)", len(large_companies))
                with col2:
                    st.metric("Medium Companies (5-9 connections)", len(medium_companies))
                with col3:
                    st.metric("Small Companies (1-4 connections)", len(small_companies))
                
                # Company growth over time
                if connections_with_dates:
                    st.markdown("### Company Connection Timeline")
                    
                    # Analyze when you connected with different companies
                    company_timeline = {}
                    for conn in connections_with_dates:
                        if conn['company'] != "Unknown Company":
                            try:
                                date = datetime.strptime(conn['raw_connected_on'], '%d %b %Y')
                                year = date.strftime('%Y')
                                
                                if year not in company_timeline:
                                    company_timeline[year] = set()
                                
                                company_timeline[year].add(conn['company'])
                            except:
                                continue
                    
                    # Show new companies by year
                    new_companies_by_year = []
                    for year in sorted(company_timeline.keys()):
                        if year == min(company_timeline.keys()):
                            new_companies = len(company_timeline[year])
                        else:
                            prev_companies = set()
                            for prev_year in company_timeline:
                                if prev_year < year:
                                    prev_companies.update(company_timeline[prev_year])
                            new_companies = len(company_timeline[year] - prev_companies)
                        
                        new_companies_by_year.append((year, new_companies))
                    
                    fig_company_growth = go.Figure(data=[
                        go.Bar(
                            x=[item[0] for item in new_companies_by_year],
                            y=[item[1] for item in new_companies_by_year],
                            marker_color='#0077b5'
                        )
                    ])
                    
                    fig_company_growth.update_layout(
                        title="New Companies Entered Your Network",
                        xaxis_title="Year",
                        yaxis_title="New Companies",
                        height=400
                    )
                    
                    st.plotly_chart(fig_company_growth, use_container_width=True)
            
            with tab3:
                # Industry Clustering
                st.markdown("### Industry Analysis")
                
                # Estimate industries based on company names and positions
                tech_keywords = ['tech', 'software', 'engineer', 'developer', 'data', 'cloud', 'ai', 'ml']
                finance_keywords = ['bank', 'financial', 'investment', 'capital', 'fund', 'analyst']
                healthcare_keywords = ['health', 'medical', 'pharma', 'clinical', 'bio', 'hospital']
                consulting_keywords = ['consulting', 'advisory', 'strategy', 'management']
                education_keywords = ['school', 'university', 'education', 'professor', 'teacher']
                
                industries = {'Technology': 0, 'Finance': 0, 'Healthcare': 0, 'Consulting': 0, 'Education': 0, 'Other': 0}
                
                for conn in connections:
                    company = conn['company'].lower()
                    title = conn['title'].lower()
                    
                    if any(keyword in company or keyword in title for keyword in tech_keywords):
                        industries['Technology'] += 1
                    elif any(keyword in company or keyword in title for keyword in finance_keywords):
                        industries['Finance'] += 1
                    elif any(keyword in company or keyword in title for keyword in healthcare_keywords):
                        industries['Healthcare'] += 1
                    elif any(keyword in company or keyword in title for keyword in consulting_keywords):
                        industries['Consulting'] += 1
                    elif any(keyword in company or keyword in title for keyword in education_keywords):
                        industries['Education'] += 1
                    else:
                        industries['Other'] += 1
                
                # Create pie chart for industries
                fig_industries = go.Figure(data=[go.Pie(
                    labels=list(industries.keys()),
                    values=list(industries.values()),
                    hole=.3
                )])
                
                fig_industries.update_layout(
                    title="Estimated Industry Distribution",
                    height=400
                )
                
                st.plotly_chart(fig_industries, use_container_width=True)
                
                # Show top titles for each industry
                for industry in industries:
                    if industries[industry] > 0:
                        st.markdown(f"**{industry} Sector Insights**")
                        # Get connections in this industry
                        industry_connections = []
                        for conn in connections:
                            company = conn['company'].lower()
                            title = conn['title'].lower()
                            
                            if industry == 'Technology' and any(keyword in company or keyword in title for keyword in tech_keywords):
                                industry_connections.append(conn)
                            elif industry == 'Finance' and any(keyword in company or keyword in title for keyword in finance_keywords):
                                industry_connections.append(conn)
                            # Add other industry checks...
                        
                        # Show top titles in this industry
                        title_counts = pd.Series([c['title'] for c in industry_connections]).value_counts().head(5)
                        if not title_counts.empty:
                            for title, count in title_counts.items():
                                st.text(f"• {title} ({count})")
            
            with tab4:
                # Recommendations
                st.markdown("### Network Growth Recommendations")
                
                # Analyze gaps and opportunities
                st.markdown("#### 🎯 Networking Opportunities")
                
                # Find underrepresented companies
                top_companies = company_counts.head(10)
                underrepresented = []
                
                for company, count in top_companies.items():
                    if count < 5:
                        underrepresented.append((company, count))
                
                if underrepresented:
                    st.markdown("**Companies to expand connections in:**")
                    for company, count in underrepresented:
                        st.text(f"• {company} (currently {count} connections)")
                
                # Find missing industries
                missing_industries = [ind for ind, count in industries.items() if count == 0]
                if missing_industries:
                    st.markdown("**Industries to explore:**")
                    for industry in missing_industries:
                        st.text(f"• {industry}")
                
                # Show connection date insights
                if connections_with_dates:
                    recent_connections = sorted(dates, reverse=True)[:10]
                    oldest_connections = sorted(dates)[:10]
                    
                    st.markdown("#### 📅 Connection Maintenance")
                    st.markdown("Consider reaching out to your oldest connections:")
                    
                    old_conn_data = []
                    for date in oldest_connections:
                        for conn in connections_with_dates:
                            try:
                                conn_date = datetime.strptime(conn['raw_connected_on'], '%d %b %Y')
                                if conn_date == date:
                                    old_conn_data.append((conn['name'], conn['company'], conn['connected_on']))
                                    break
                            except:
                                continue
                    
                    for name, company, connected_on in old_conn_data[:5]:
                        st.text(f"• {name} from {company} (connected {connected_on})")
                
                # Show email collection opportunities
                no_email_count = len([c for c in connections if not c['email']])
                st.markdown(f"#### 📧 Contact Information")
                st.markdown(f"You're missing email addresses for {no_email_count} connections. Consider:")
                st.text("• Sending LinkedIn messages to request contact info")
                st.text("• Updating your privacy settings to share your email")
                st.text("• Using LinkedIn's 'Ask for contact info' feature")
            
            # Export options
            st.subheader("Export Options")
            if st.button("Export Network Data"):
                # Create export data
                export_data = {
                    "main_person": main_person_data,
                    "connections": connections,
                    "statistics": {
                        "total_connections": len(connections),
                        "unique_companies": unique_companies,
                        "with_email": with_email,
                        "with_url": with_url,
                        "top_companies": dict(top_companies.head(5)),
                        "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                }
                
                st.download_button(
                    label="Download Network JSON",
                    data=pd.DataFrame([export_data]).to_json(orient='records', indent=2),
                    file_name=f"linkedin_network_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
    
    except Exception as e:
        st.error(f"Error processing the file: {str(e)}")
        st.info("Please make sure you've uploaded the correct Connections.csv file from your LinkedIn data download.")
        
        # Debug info
        if st.checkbox("Show debug information"):
            st.text(f"Error: {str(e)}")
            import traceback
            st.text(traceback.format_exc())
            
            # Show first few lines of the file
            st.subheader("First 10 lines of your file:")
            try:
                uploaded_file.seek(0)
                content = uploaded_file.read()
                lines = content.decode('utf-8', errors='replace').split('\n')[:10]
                for i, line in enumerate(lines, 1):
                    st.text(f"Line {i}: {line}")
            except:
                try:
                    uploaded_file.seek(0)
                    content = uploaded_file.read()
                    lines = content.decode('latin-1', errors='replace').split('\n')[:10]
                    for i, line in enumerate(lines, 1):
                        st.text(f"Line {i}: {line}")
                except:
                    st.text("Unable to read file content for debugging")

# Display selected node information
if st.session_state.selected_node and st.session_state.graph_data:
    node_data = st.session_state.graph_data.nodes[st.session_state.selected_node]
    
    # Determine card style based on node type
    card_class = "main-card" if node_data['type'] == 'main' else "connection-card"
    
    st.markdown(f"""
    <div class="person-card {card_class}">
        <div class="card-header">
            <h3>{node_data['name']}</h3>
            <span class="badge">{node_data['type'].title()}</span>
        </div>
        <div class="card-body">
            <h5>{node_data['title']} <span class="company-badge">{node_data['company']}</span></h5>
            <p><strong>📍 Location:</strong> {node_data['location']}</p>
            <p><strong>✉️ Email:</strong> {node_data['email'] if node_data['email'] else 'Not available / Not shared'}</p>
            <p><strong>🔗 LinkedIn URL:</strong> {f'<a href="{node_data["url"]}" target="_blank" class="url-link">{node_data["url"]}</a>' if node_data['url'] else 'Not available'}</p>
            <p><strong>📅 Connected on:</strong> {node_data.get('connected_on', 'Date not available')}</p>
            <p><strong>📚 Experience:</strong> {node_data['experience']}</p>
            <p><strong>🎓 Education:</strong> {node_data['education']}</p>
            <div>
                <strong>🛠️ Skills:</strong>
                <div style="margin-top: 5px;">
                    {' '.join([f'<span class="badge" style="margin: 2px;">{skill}</span>' for skill in node_data['skills']])}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    st.info("Upload your LinkedIn Connections.csv file to get started. This file can be obtained by requesting a copy of your LinkedIn data.")

# Footer
st.markdown("---")
st.markdown("Your data is processed locally and never stored on external servers.")
