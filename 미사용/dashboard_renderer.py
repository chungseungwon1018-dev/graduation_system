import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.offline as pyo
from typing import Dict, List, Optional
import base64
from io import BytesIO
import json

plt.rcParams['font.family'] = 'DejaVu Sans'
sns.set_style("whitegrid")
sns.set_palette("husl")

class DashboardRenderer:
    def __init__(self, use_plotly: bool = True):
        self.use_plotly = use_plotly
        self.colors = {
            'fulfilled': '#2E8B57',      # Sea Green
            'partial': '#FF8C00',        # Dark Orange  
            'unfulfilled': '#DC143C',    # Crimson
            'background': '#F8F9FA',     # Light Gray
            'text': '#2C3E50'           # Dark Blue Gray
        }
    
    def render_graduation_dashboard(self, analysis_result: Dict) -> Dict[str, str]:
        if 'error' in analysis_result:
            return {"error": analysis_result['error']}
        
        dashboard_data = {
            "student_info": self._render_student_info_table(analysis_result),
            "completion_overview": self._render_completion_overview(analysis_result),
            "requirements_table": self._render_requirements_table(analysis_result),
            "credit_breakdown_chart": self._render_credit_breakdown_chart(analysis_result),
            "completion_rate_chart": self._render_completion_rate_chart(analysis_result),
            "recommendations": self._render_recommendations(analysis_result)
        }
        
        if self.use_plotly:
            dashboard_data["interactive_dashboard"] = self._render_interactive_dashboard(analysis_result)
        
        return dashboard_data
    
    def _render_student_info_table(self, analysis_result: Dict) -> str:
        student_info = analysis_result.get('student_info', {})
        
        html = """
        <div class="student-info-card">
            <h3>학생 정보</h3>
            <table class="info-table">
                <tr><td><strong>학번</strong></td><td>{student_id}</td></tr>
                <tr><td><strong>성명</strong></td><td>{name}</td></tr>
                <tr><td><strong>학과</strong></td><td>{department}</td></tr>
                <tr><td><strong>전공</strong></td><td>{major}</td></tr>
                <tr><td><strong>학년</strong></td><td>{grade}</td></tr>
                <tr><td><strong>입학일자</strong></td><td>{admission_date}</td></tr>
                <tr><td><strong>분석일시</strong></td><td>{analysis_date}</td></tr>
            </table>
        </div>
        """.format(
            student_id=student_info.get('student_id', 'N/A'),
            name=student_info.get('name', 'N/A'),
            department=student_info.get('department', 'N/A'),
            major=student_info.get('major', 'N/A'),
            grade=student_info.get('grade', 'N/A'),
            admission_date=student_info.get('admission_date', 'N/A'),
            analysis_date=analysis_result.get('analysis_date', 'N/A')[:19]
        )
        
        return html
    
    def _render_completion_overview(self, analysis_result: Dict) -> str:
        total_completed = analysis_result.get('total_completed_credits', 0)
        total_required = analysis_result.get('total_required_credits', 0)
        completion_rate = analysis_result.get('overall_completion_rate', 0)
        missing_count = len(analysis_result.get('missing_requirements', []))
        
        status_class = "excellent" if completion_rate >= 90 else "good" if completion_rate >= 70 else "warning" if completion_rate >= 50 else "danger"
        
        html = f"""
        <div class="completion-overview {status_class}">
            <h3>졸업요건 이수 현황</h3>
            <div class="overview-grid">
                <div class="metric-card">
                    <div class="metric-value">{completion_rate:.1f}%</div>
                    <div class="metric-label">전체 이수율</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{total_completed:.1f}</div>
                    <div class="metric-label">이수학점</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{total_required:.1f}</div>
                    <div class="metric-label">필요학점</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{missing_count}</div>
                    <div class="metric-label">미충족 영역</div>
                </div>
            </div>
        </div>
        """
        
        return html
    
    def _render_requirements_table(self, analysis_result: Dict) -> str:
        requirements = analysis_result.get('requirements_analysis', [])
        
        html = """
        <div class="requirements-table-container">
            <h3>영역별 이수현황</h3>
            <table class="requirements-table">
                <thead>
                    <tr>
                        <th>구분</th>
                        <th>영역</th>
                        <th>필요학점</th>
                        <th>이수학점</th>
                        <th>부족학점</th>
                        <th>이수율</th>
                        <th>상태</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for req in requirements:
            status = "충족" if req['is_fulfilled'] else "미충족"
            status_class = "fulfilled" if req['is_fulfilled'] else "unfulfilled"
            completion_rate = req['completion_rate']
            
            html += f"""
                <tr class="{status_class}">
                    <td>{req['category']}</td>
                    <td>{req['area'] or '-'}</td>
                    <td>{req['required_credits']:.1f}</td>
                    <td>{req['completed_credits']:.1f}</td>
                    <td>{req['missing_credits']:.1f}</td>
                    <td>{completion_rate:.1f}%</td>
                    <td><span class="status-badge {status_class}">{status}</span></td>
                </tr>
            """
        
        html += """
                </tbody>
            </table>
        </div>
        """
        
        return html
    
    def _render_credit_breakdown_chart(self, analysis_result: Dict) -> str:
        requirements = analysis_result.get('requirements_analysis', [])
        
        if self.use_plotly:
            return self._render_plotly_credit_breakdown(requirements)
        else:
            return self._render_matplotlib_credit_breakdown(requirements)
    
    def _render_plotly_credit_breakdown(self, requirements: List[Dict]) -> str:
        categories = []
        completed = []
        required = []
        
        for req in requirements:
            label = f"{req['category']}"
            if req['area']:
                label += f" - {req['area']}"
            categories.append(label)
            completed.append(req['completed_credits'])
            required.append(req['required_credits'])
        
        fig = go.Figure(data=[
            go.Bar(name='이수학점', x=categories, y=completed, marker_color=self.colors['fulfilled']),
            go.Bar(name='필요학점', x=categories, y=required, marker_color=self.colors['partial'], opacity=0.7)
        ])
        
        fig.update_layout(
            title="영역별 학점 이수 현황",
            xaxis_title="영역",
            yaxis_title="학점",
            barmode='group',
            height=400,
            template="plotly_white"
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id="credit-breakdown-chart")
    
    def _render_matplotlib_credit_breakdown(self, requirements: List[Dict]) -> str:
        categories = []
        completed = []
        required = []
        
        for req in requirements:
            label = f"{req['category']}"
            if req['area']:
                label += f"\n{req['area']}"
            categories.append(label)
            completed.append(req['completed_credits'])
            required.append(req['required_credits'])
        
        fig, ax = plt.subplots(figsize=(12, 6))
        x = range(len(categories))
        width = 0.35
        
        ax.bar([i - width/2 for i in x], completed, width, label='이수학점', color=self.colors['fulfilled'])
        ax.bar([i + width/2 for i in x], required, width, label='필요학점', color=self.colors['partial'], alpha=0.7)
        
        ax.set_xlabel('영역')
        ax.set_ylabel('학점')
        ax.set_title('영역별 학점 이수 현황')
        ax.set_xticks(x)
        ax.set_xticklabels(categories, rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return f'<img src="data:image/png;base64,{image_base64}" alt="Credit Breakdown Chart" class="chart-image">'
    
    def _render_completion_rate_chart(self, analysis_result: Dict) -> str:
        requirements = analysis_result.get('requirements_analysis', [])
        
        if self.use_plotly:
            return self._render_plotly_completion_rate(requirements)
        else:
            return self._render_matplotlib_completion_rate(requirements)
    
    def _render_plotly_completion_rate(self, requirements: List[Dict]) -> str:
        categories = []
        rates = []
        colors = []
        
        for req in requirements:
            label = f"{req['category']}"
            if req['area']:
                label += f" - {req['area']}"
            categories.append(label)
            rate = req['completion_rate']
            rates.append(rate)
            
            if rate >= 100:
                colors.append(self.colors['fulfilled'])
            elif rate >= 70:
                colors.append(self.colors['partial'])
            else:
                colors.append(self.colors['unfulfilled'])
        
        fig = go.Figure(data=[go.Bar(x=categories, y=rates, marker_color=colors)])
        
        fig.update_layout(
            title="영역별 이수율",
            xaxis_title="영역",
            yaxis_title="이수율 (%)",
            height=400,
            template="plotly_white"
        )
        
        fig.add_hline(y=100, line_dash="dash", line_color="green", 
                     annotation_text="목표 달성선", annotation_position="top right")
        
        return fig.to_html(include_plotlyjs='cdn', div_id="completion-rate-chart")
    
    def _render_matplotlib_completion_rate(self, requirements: List[Dict]) -> str:
        categories = []
        rates = []
        colors = []
        
        for req in requirements:
            label = f"{req['category']}"
            if req['area']:
                label += f"\n{req['area']}"
            categories.append(label)
            rate = req['completion_rate']
            rates.append(rate)
            
            if rate >= 100:
                colors.append(self.colors['fulfilled'])
            elif rate >= 70:
                colors.append(self.colors['partial'])
            else:
                colors.append(self.colors['unfulfilled'])
        
        fig, ax = plt.subplots(figsize=(12, 6))
        bars = ax.bar(categories, rates, color=colors)
        
        ax.set_xlabel('영역')
        ax.set_ylabel('이수율 (%)')
        ax.set_title('영역별 이수율')
        ax.set_xticklabels(categories, rotation=45, ha='right')
        ax.axhline(y=100, color='green', linestyle='--', alpha=0.7, label='목표 달성선')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        for bar, rate in zip(bars, rates):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                   f'{rate:.1f}%', ha='center', va='bottom')
        
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return f'<img src="data:image/png;base64,{image_base64}" alt="Completion Rate Chart" class="chart-image">'
    
    def _render_recommendations(self, analysis_result: Dict) -> str:
        recommendations = analysis_result.get('recommendations', [])
        
        if not recommendations:
            return "<div class='recommendations'><h3>추천사항</h3><p>추천사항이 없습니다.</p></div>"
        
        html = """
        <div class="recommendations">
            <h3>추천사항</h3>
            <ul class="recommendation-list">
        """
        
        for rec in recommendations:
            html += f"<li>{rec}</li>"
        
        html += """
            </ul>
        </div>
        """
        
        return html
    
    def _render_interactive_dashboard(self, analysis_result: Dict) -> str:
        requirements = analysis_result.get('requirements_analysis', [])
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('이수율 현황', '학점 비교', '영역별 상태', '전체 진행률'),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "pie"}, {"type": "indicator"}]]
        )
        
        categories = [f"{req['category']}-{req['area']}" if req['area'] else req['category'] for req in requirements]
        completion_rates = [req['completion_rate'] for req in requirements]
        completed_credits = [req['completed_credits'] for req in requirements]
        required_credits = [req['required_credits'] for req in requirements]
        
        colors = [self.colors['fulfilled'] if rate >= 100 else 
                 self.colors['partial'] if rate >= 70 else 
                 self.colors['unfulfilled'] for rate in completion_rates]
        
        fig.add_trace(go.Bar(x=categories, y=completion_rates, marker_color=colors, name="이수율"), row=1, col=1)
        fig.add_trace(go.Bar(x=categories, y=completed_credits, name="이수학점", marker_color=self.colors['fulfilled']), row=1, col=2)
        fig.add_trace(go.Bar(x=categories, y=required_credits, name="필요학점", marker_color=self.colors['partial']), row=1, col=2)
        
        fulfilled_count = sum(1 for req in requirements if req['is_fulfilled'])
        unfulfilled_count = len(requirements) - fulfilled_count
        
        fig.add_trace(go.Pie(labels=['충족', '미충족'], values=[fulfilled_count, unfulfilled_count],
                            marker_colors=[self.colors['fulfilled'], self.colors['unfulfilled']]), row=2, col=1)
        
        overall_rate = analysis_result.get('overall_completion_rate', 0)
        fig.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=overall_rate,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "전체 이수율 (%)"},
            gauge={'axis': {'range': [None, 100]},
                   'bar': {'color': self.colors['fulfilled']},
                   'steps': [{'range': [0, 50], 'color': self.colors['unfulfilled']},
                            {'range': [50, 80], 'color': self.colors['partial']},
                            {'range': [80, 100], 'color': self.colors['fulfilled']}],
                   'threshold': {'line': {'color': "red", 'width': 4},
                                'thickness': 0.75, 'value': 90}}), row=2, col=2)
        
        fig.update_layout(height=800, showlegend=True, title_text="졸업요건 분석 대시보드")
        
        return fig.to_html(include_plotlyjs='cdn', div_id="interactive-dashboard")
    
    def generate_css(self) -> str:
        return """
        <style>
        .student-info-card {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        
        .info-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .info-table td {
            padding: 8px 12px;
            border-bottom: 1px solid #eee;
        }
        
        .completion-overview {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            padding: 24px;
            margin: 20px 0;
        }
        
        .overview-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .metric-card {
            background: rgba(255,255,255,0.1);
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        }
        
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 8px;
        }
        
        .metric-label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        
        .requirements-table-container {
            margin: 20px 0;
            overflow-x: auto;
        }
        
        .requirements-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }
        
        .requirements-table th {
            background: #343a40;
            color: white;
            padding: 12px;
            text-align: left;
        }
        
        .requirements-table td {
            padding: 12px;
            border-bottom: 1px solid #eee;
        }
        
        .requirements-table tr.fulfilled {
            background-color: #d4edda;
        }
        
        .requirements-table tr.unfulfilled {
            background-color: #f8d7da;
        }
        
        .status-badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: bold;
        }
        
        .status-badge.fulfilled {
            background: #28a745;
            color: white;
        }
        
        .status-badge.unfulfilled {
            background: #dc3545;
            color: white;
        }
        
        .chart-image {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .recommendations {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        
        .recommendation-list {
            margin: 0;
            padding-left: 20px;
        }
        
        .recommendation-list li {
            margin: 8px 0;
            line-height: 1.5;
        }
        
        .excellent { border-left: 5px solid #28a745; }
        .good { border-left: 5px solid #17a2b8; }
        .warning { border-left: 5px solid #ffc107; }
        .danger { border-left: 5px solid #dc3545; }
        </style>
        """

def render_student_dashboard(analysis_result: Dict, use_plotly: bool = True) -> str:
    renderer = DashboardRenderer(use_plotly=use_plotly)
    dashboard_data = renderer.render_graduation_dashboard(analysis_result)
    
    if "error" in dashboard_data:
        return f"<div class='error'>오류: {dashboard_data['error']}</div>"
    
    css = renderer.generate_css()
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>졸업학점 분석 대시보드</title>
        {css}
    </head>
    <body>
        <div class="dashboard-container">
            <h1>졸업학점 분석 대시보드</h1>
            
            {dashboard_data['student_info']}
            {dashboard_data['completion_overview']}
            {dashboard_data['requirements_table']}
            
            <div class="charts-section">
                <h3>분석 차트</h3>
                {dashboard_data['credit_breakdown_chart']}
                {dashboard_data['completion_rate_chart']}
            </div>
            
            {dashboard_data['recommendations']}
            
            {dashboard_data.get('interactive_dashboard', '')}
        </div>
    </body>
    </html>
    """
    
    return html

if __name__ == "__main__":
    sample_analysis = {
        "student_info": {
            "student_id": "2023001",
            "name": "김학생",
            "department": "컴퓨터공학과",
            "major": "컴퓨터공학",
            "grade": 3,
            "admission_date": "2023-03-01"
        },
        "analysis_date": "2025-06-02T10:30:00",
        "total_completed_credits": 95.0,
        "total_required_credits": 128.0,
        "overall_completion_rate": 74.2,
        "requirements_analysis": [
            {
                "category": "교양",
                "area": "기초교양",
                "required_credits": 15.0,
                "completed_credits": 15.0,
                "missing_credits": 0.0,
                "is_fulfilled": True,
                "completion_rate": 100.0
            },
            {
                "category": "전공",
                "area": "전공필수",
                "required_credits": 45.0,
                "completed_credits": 36.0,
                "missing_credits": 9.0,
                "is_fulfilled": False,
                "completion_rate": 80.0
            }
        ],
        "recommendations": [
            "전공 전공필수 영역에서 9학점이 부족합니다. 해당 영역의 교과목을 추가로 수강하세요.",
            "졸업까지 총 33학점이 부족합니다."
        ]
    }
    
    dashboard_html = render_student_dashboard(sample_analysis)
    
    with open("sample_dashboard.html", "w", encoding="utf-8") as f:
        f.write(dashboard_html)
    
    print("샘플 대시보드가 sample_dashboard.html로 생성되었습니다.")