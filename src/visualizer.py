import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Visualizer:
    """
    Creates interactive visualizations for different types of queries
    """
    
    def __init__(self):
        self.color_palette = px.colors.qualitative.Set2
        self.template = "plotly_white"
    
    def create_visualizations(self, parsed_query: Dict, analysis_results: Dict) -> List:
        """
        Create appropriate visualizations based on query type and analysis
        """
        visualizations = []
        intent = parsed_query['intent']
        
        try:
            if intent == 'compare':
                visualizations.extend(self._create_comparison_charts(parsed_query, analysis_results))
            elif intent == 'top':
                visualizations.extend(self._create_ranking_charts(parsed_query, analysis_results))
            elif intent == 'trend':
                visualizations.extend(self._create_trend_charts(parsed_query, analysis_results))
            elif intent == 'correlation':
                visualizations.extend(self._create_correlation_charts(parsed_query, analysis_results))
            else:
                visualizations.extend(self._create_general_charts(parsed_query, analysis_results))
        
        except Exception as e:
            logger.error(f"Error creating visualizations: {e}")
        
        return visualizations
    
    def _create_comparison_charts(self, parsed_query: Dict, analysis: Dict) -> List:
        """Create charts for comparison analysis"""
        charts = []
        summary = analysis.get('summary', {})
        
        # Rainfall comparison bar chart
        if 'rainfall_comparison' in summary:
            rainfall_data = summary['rainfall_comparison']
            
            fig = go.Figure(data=[
                go.Bar(
                    x=list(rainfall_data.keys()),
                    y=list(rainfall_data.values()),
                    marker_color=self.color_palette[0],
                    text=[f"{v:.1f} mm" for v in rainfall_data.values()],
                    textposition='auto',
                )
            ])
            
            fig.update_layout(
                title="Average Annual Rainfall Comparison",
                xaxis_title="State",
                yaxis_title="Rainfall (mm)",
                template=self.template,
                height=400
            )
            
            charts.append(fig)
        
        # Crop production comparison
        if 'crop_comparison' in summary:
            crop_data = summary['crop_comparison']
            
            # Create grouped bar chart
            fig = go.Figure()
            
            for state, crops in crop_data.items():
                crop_names = [c['crop'] for c in crops[:5]]
                productions = [c['production'] for c in crops[:5]]
                
                fig.add_trace(go.Bar(
                    name=state,
                    x=crop_names,
                    y=productions,
                    text=[f"{p:,.0f}" for p in productions],
                    textposition='auto'
                ))
            
            fig.update_layout(
                title="Top Crop Production by State",
                xaxis_title="Crop",
                yaxis_title="Production (tonnes)",
                barmode='group',
                template=self.template,
                height=500
            )
            
            charts.append(fig)
        
        return charts
    
    def _create_ranking_charts(self, parsed_query: Dict, analysis: Dict) -> List:
        """Create charts for top-N ranking"""
        charts = []
        
        if 'top_results' in analysis:
            top_results = analysis['top_results']
            
            names = [r['name'] for r in top_results]
            values = [r['value'] for r in top_results]
            unit = top_results[0].get('unit', '') if top_results else ''
            
            # Horizontal bar chart for rankings
            fig = go.Figure(data=[
                go.Bar(
                    x=values,
                    y=names,
                    orientation='h',
                    marker_color=self.color_palette[1],
                    text=[f"{v:,.1f} {unit}" for v in values],
                    textposition='auto'
                )
            ])
            
            fig.update_layout(
                title=f"Top {len(top_results)} Rankings",
                xaxis_title=f"Value ({unit})",
                yaxis_title="",
                template=self.template,
                height=400
            )
            
            # Reverse y-axis to show highest at top
            fig.update_yaxes(autorange="reversed")
            
            charts.append(fig)
            
            # Also create a pie chart
            fig_pie = go.Figure(data=[
                go.Pie(
                    labels=names,
                    values=values,
                    hole=0.3,
                    marker_colors=self.color_palette
                )
            ])
            
            fig_pie.update_layout(
                title=f"Distribution - Top {len(top_results)}",
                template=self.template,
                height=400
            )
            
            charts.append(fig_pie)
        
        return charts
    
    def _create_trend_charts(self, parsed_query: Dict, analysis: Dict) -> List:
        """Create charts for trend analysis"""
        charts = []
        
        if 'trend_summary' in analysis:
            trend = analysis['trend_summary']
            
            if 'yearly_data' in trend:
                years = list(trend['yearly_data'].keys())
                values = list(trend['yearly_data'].values())
                
                # Line chart with trend
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=years,
                    y=values,
                    mode='lines+markers',
                    name='Actual',
                    line=dict(color=self.color_palette[0], width=3),
                    marker=dict(size=8)
                ))
                
                # Add trend line
                z = np.polyfit(years, values, 1)
                p = np.poly1d(z)
                trend_line = p(years)
                
                fig.add_trace(go.Scatter(
                    x=years,
                    y=trend_line,
                    mode='lines',
                    name='Trend',
                    line=dict(color=self.color_palette[1], width=2, dash='dash')
                ))
                
                fig.update_layout(
                    title=f"Trend Analysis ({trend['start_year']}-{trend['end_year']})",
                    xaxis_title="Year",
                    yaxis_title="Value",
                    template=self.template,
                    height=400,
                    hovermode='x unified'
                )
                
                # Add annotation for growth rate
                fig.add_annotation(
                    text=f"Avg Growth: {trend['growth_rate']:.2f}%/year",
                    xref="paper", yref="paper",
                    x=0.02, y=0.98,
                    showarrow=False,
                    bgcolor="white",
                    bordercolor=self.color_palette[0],
                    borderwidth=2
                )
                
                charts.append(fig)
        
        return charts
    
    def _create_correlation_charts(self, parsed_query: Dict, analysis: Dict) -> List:
        """Create charts for correlation analysis"""
        charts = []
        
        if 'correlation_results' in analysis:
            corr_results = analysis['correlation_results']
            
            # Try to get the merged data for scatter plot
            data_dict = analysis.get('data', {})
            
            if 'rainfall' in data_dict and 'production' in data_dict:
                rainfall_df = data_dict['rainfall']['dataframe']
                production_df = data_dict['production']['dataframe']
                
                # Merge for visualization
                merged = pd.merge(
                    rainfall_df,
                    production_df,
                    on=['state', 'year'],
                    how='inner'
                )
                
                if not merged.empty:
                    # Scatter plot
                    fig = px.scatter(
                        merged,
                        x='annual_rainfall_mm',
                        y='production_tonnes',
                        color='state',
                        size='production_tonnes',
                        hover_data=['year'],
                        title=f"Rainfall vs Production Correlation (r={corr_results['correlation_coefficient']:.3f})",
                        labels={
                            'annual_rainfall_mm': 'Annual Rainfall (mm)',
                            'production_tonnes': 'Production (tonnes)'
                        },
                        template=self.template,
                        height=500
                    )
                    
                    # Add trend line
                    fig.update_traces(marker=dict(size=10, line=dict(width=1, color='white')))
                    
                    charts.append(fig)
        
        return charts
    
    def _create_general_charts(self, parsed_query: Dict, analysis: Dict) -> List:
        """Create general purpose charts"""
        charts = []
        data_dict = analysis.get('data', {})
        
        for key, data_info in data_dict.items():
            if isinstance(data_info, dict) and 'dataframe' in data_info:
                df = data_info['dataframe']
                
                if not df.empty:
                    # Create a simple overview chart
                    numeric_cols = df.select_dtypes(include=['number']).columns
                    
                    if len(numeric_cols) > 0:
                        # Bar chart of first numeric column by categorical column
                        cat_cols = df.select_dtypes(include=['object']).columns
                        
                        if len(cat_cols) > 0 and len(numeric_cols) > 0:
                            cat_col = cat_cols[0]
                            num_col = numeric_cols[0]
                            
                            agg_data = df.groupby(cat_col)[num_col].sum().sort_values(ascending=False).head(10)
                            
                            fig = go.Figure(data=[
                                go.Bar(
                                    x=agg_data.index,
                                    y=agg_data.values,
                                    marker_color=self.color_palette[2]
                                )
                            ])
                            
                            fig.update_layout(
                                title=f"{num_col.replace('_', ' ').title()} by {cat_col.replace('_', ' ').title()}",
                                xaxis_title=cat_col.replace('_', ' ').title(),
                                yaxis_title=num_col.replace('_', ' ').title(),
                                template=self.template,
                                height=400
                            )
                            
                            charts.append(fig)
        
        return charts
    
    def create_heatmap(self, df: pd.DataFrame, x_col: str, y_col: str, value_col: str, title: str) -> go.Figure:
        """Create a heatmap visualization"""
        pivot_df = df.pivot_table(values=value_col, index=y_col, columns=x_col, aggfunc='sum')
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot_df.values,
            x=pivot_df.columns,
            y=pivot_df.index,
            colorscale='Viridis',
            text=pivot_df.values,
            texttemplate='%{text:.0f}',
            textfont={"size": 10}
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title=x_col.replace('_', ' ').title(),
            yaxis_title=y_col.replace('_', ' ').title(),
            template=self.template,
            height=500
        )
        
        return fig
    
    def create_time_series(self, df: pd.DataFrame, time_col: str, value_col: str, 
                          group_col: Optional[str] = None, title: str = "") -> go.Figure:
        """Create a time series visualization"""
        fig = go.Figure()
        
        if group_col and group_col in df.columns:
            for group in df[group_col].unique():
                group_data = df[df[group_col] == group].sort_values(time_col)
                fig.add_trace(go.Scatter(
                    x=group_data[time_col],
                    y=group_data[value_col],
                    mode='lines+markers',
                    name=str(group),
                    line=dict(width=2),
                    marker=dict(size=6)
                ))
        else:
            sorted_df = df.sort_values(time_col)
            fig.add_trace(go.Scatter(
                x=sorted_df[time_col],
                y=sorted_df[value_col],
                mode='lines+markers',
                line=dict(width=3),
                marker=dict(size=8)
            ))
        
        fig.update_layout(
            title=title or f"{value_col.replace('_', ' ').title()} Over Time",
            xaxis_title=time_col.replace('_', ' ').title(),
            yaxis_title=value_col.replace('_', ' ').title(),
            template=self.template,
            height=400,
            hovermode='x unified'
        )
        
        return fig


# Import numpy for trend line calculation
import numpy as np