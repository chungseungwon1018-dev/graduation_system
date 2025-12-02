import mysql.connector
from mysql.connector import Error
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GraduationRequirementsChecker:
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.connection = None

    def connect_db(self):
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            logger.info("MySQL 데이터베이스 연결 성공")
        except Error as e:
            logger.error(f"MySQL 연결 오류: {e}")
            raise

    def disconnect_db(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("MySQL 연결 해제")

    def get_student_info(self, student_id: str) -> Optional[Dict]:
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM students WHERE student_id = %s", (student_id,))
            result = cursor.fetchone()
            cursor.close()
            return result
        except Error as e:
            logger.error(f"학생 정보 조회 오류: {e}")
            return None

    def get_student_courses(self, student_id: str) -> List[Dict]:
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM course_records WHERE student_id = %s", (student_id,))
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            logger.error(f"학생 수강 기록 조회 오류: {e}")
            return []

    def get_graduation_requirements(self, department: str, admission_year: int) -> List[Dict]:
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT * FROM graduation_requirements 
            WHERE department = %s AND admission_year = %s
            ORDER BY category, area
            """
            cursor.execute(query, (department, admission_year))
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            logger.error(f"졸업 요건 조회 오류: {e}")
            return []

    def get_major_elective_recognition(self, department: str, admission_year: int) -> Dict[str, Dict]:
        """인정 규칙을 admission_year에 맞는 범위로 조회.
        반환:
            {
                'rules': [ {source_college, required_type_source, ...}, ...],
                'courses': [ {source_department, course_code, ...}, ...]
            }
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT * FROM major_elective_recognition
            WHERE department = %s
              AND admission_year_from <= %s
              AND admission_year_to >= %s
              AND is_active = TRUE
            """
            cursor.execute(query, (department, admission_year, admission_year))
            rows = cursor.fetchall()
            cursor.close()
            rules = []
            courses = []
            for r in rows:
                if r.get('rule_type') == '규칙':
                    rules.append(r)
                else:
                    courses.append(r)
            return {'rules': rules, 'courses': courses}
        except Error as e:
            logger.error(f"전선 인정 규칙 조회 오류: {e}")
            return {'rules': [], 'courses': []}

    def get_curriculum_courses(self, department: str, admission_year: int) -> List[Dict]:
        """입학년도 범위에 해당하는 커리큘럼 과목 조회"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT * FROM curriculum_courses
            WHERE department = %s
              AND admission_year_from <= %s
              AND admission_year_to >= %s
              AND is_active = TRUE
            ORDER BY grade_year, term, required_type, course_code
            """
            cursor.execute(query, (department, admission_year, admission_year))
            rows = cursor.fetchall()
            cursor.close()
            return rows
        except Error as e:
            logger.error(f"커리큘럼 과목 조회 오류: {e}")
            return []

    def analyze_graduation_status(self, student_id: str, parsing_warnings: Optional[List[str]] = None) -> Dict:
        student_info = self.get_student_info(student_id)
        if not student_info:
            return {"error": "학생 정보를 찾을 수 없습니다."}

        student_courses = self.get_student_courses(student_id)
        admission_year = self._extract_admission_year(student_info.get('admission_date'))
        graduation_requirements = self.get_graduation_requirements(student_info.get('department'), admission_year)
        recognition = self.get_major_elective_recognition(student_info.get('department'), admission_year)

        if not graduation_requirements:
            return {"error": "해당 학과의 졸업 요건을 찾을 수 없습니다."}

        # 교양 상한(cap) 추출
        liberal_caps = []
        for r in graduation_requirements:
            if str(r.get('category')) == '교양' and r.get('max_credits') is not None:
                try:
                    liberal_caps.append(float(r.get('max_credits')))
                except:
                    pass
        precomputed_liberal_cap = max(liberal_caps) if liberal_caps else 40.0

        # 졸업이수학점(예: 130) 추출 (요건표에서 category/area에 '졸업' 또는 '총계' 등으로 표시된 행)
        grad_total_credit = None
        for r in graduation_requirements:
            if (str(r.get('category')).find('졸업') != -1 or str(r.get('area')).find('졸업') != -1 or str(r.get('category')).find('총계') != -1):
                try:
                    grad_total_credit = float(r.get('required_credits'))
                    break
                except:
                    pass
        if grad_total_credit is None:
            grad_total_credit = 130.0  # 기본값

        # 집계용 행(총계, 합계 등) 제외
        exclude_keywords = ['총계', '합계', '학점총계', '교양총계', '졸업']
        filtered_requirements = [r for r in graduation_requirements if not any(
            (str(r.get('area', '')) + str(r.get('category', ''))).find(k) != -1 for k in exclude_keywords)]

        analysis_result = {
            "student_info": student_info,
            "analysis_date": datetime.now().isoformat(),
            "requirements_analysis": [],
            "total_completed_credits": 0.0,
            "total_required_credits": grad_total_credit,
            "overall_completion_rate": 0.0,
            "missing_requirements": [],
            "recommendations": [],
            "liberal_arts_detail": {},
            "major_detail": {},
            "parsing_warnings": parsing_warnings or [],
        }

        # 타학과 인정 규칙 반영: 규칙형(단과대 전필→전선), 개별과목형(특정 과목 전선 인정)
        adjusted_courses = self._apply_recognition_rules(student_courses, recognition)
        completed_credits_by_category = self._calculate_completed_credits(adjusted_courses)

        # 전공필수/전공선택/일반선택 구분 (엑셀 AC22, AH22, Y22 셀 값 사용)
        # students 테이블의 major_required_credits, major_elective_credits, general_elective_credits에서 가져옴
        major_required = float(student_info.get('major_required_credits', 0)) if student_info.get('major_required_credits') else 0.0
        major_elective = float(student_info.get('major_elective_credits', 0)) if student_info.get('major_elective_credits') else 0.0
        general_elective = float(student_info.get('general_elective_credits', 0)) if student_info.get('general_elective_credits') else 0.0

        analysis_result["major_detail"] = {
            "전공필수": major_required,
            "전공선택": major_elective
        }
        
        analysis_result["general_elective_detail"] = {
            "일반선택": general_elective
        }

        # 교양 영역별 집계 및 상한 적용
        used_keys = set()
        교양_요건_키 = set()
        교양_상한 = precomputed_liberal_cap
        교양_이수합 = 0.0
        기타_교양_이수합 = 0.0
        비교양_이수합 = 0.0
        liberal_arts_detail = {}


        # 개신기초교양 세부영역을 총합으로 평가하기 위해 개별 항목을 모아둠
        gsin_basic_requirements = []

        # 개신기초교양 세부영역 표준화 매핑
        gsin_basic_map = {
            '인성과 비판적 사고': '인성과 비판적 사고',
            '인성과비판적사고': '인성과 비판적 사고',
            '의사소통': '의사소통',
            '영어': '영어',
            '정보문해': '정보문해'
        }
        gsin_parts_credits = {k: 0.0 for k in ['인성과 비판적 사고','의사소통','영어','정보문해']}
        # 코스 기반으로 개신기초교양 세부영역 집계
        try:
            for c in adjusted_courses:
                if (c.get('category') == '교양') and ((c.get('area') or '').strip() == '개신기초교양') and self._is_passed_course(c):
                    sub = (c.get('sub_area') or '').strip()
                    sub_std = gsin_basic_map.get(sub, sub)
                    if sub_std in gsin_parts_credits:
                        gsin_parts_credits[sub_std] += float(c.get('credit') or 0.0)
        except Exception:
            pass

        for requirement in filtered_requirements:
            category = requirement.get('category')
            area = requirement.get('area', '')
            required_credits = float(requirement.get('required_credits', 0))
            max_credits = requirement.get('max_credits')
            key = f"{category}_{area}" if area else category
            if key in used_keys:
                continue
            used_keys.add(key)

            if category == '교양':
                교양_요건_키.add(key)
                if max_credits is not None:
                    try:
                        max_credits_val = float(max_credits)
                        if 교양_상한 is None or max_credits_val > 교양_상한:
                            교양_상한 = max_credits_val
                    except:
                        pass

            # 전공필수/전공선택은 Excel에서 읽은 값 사용
            if category == '전공' and area == '전공필수':
                completed = major_required
            elif category == '전공' and area == '전공선택':
                completed = major_elective
            # 일반선택(일선)은 Excel Y22 값 사용
            elif category == '일선':
                completed = general_elective
            else:
                completed = float(completed_credits_by_category.get(key, 0.0))
                if max_credits is not None:
                    try:
                        max_credits_val = float(max_credits)
                        completed = min(completed, max_credits_val)
                    except:
                        pass

            # 개신기초교양은 세부영역을 합산하여 총 12학점 등으로 판정
            if category == '교양' and ('개신기초교양' in (area or '')):
                gsin_basic_requirements.append({
                    "required_credits": required_credits,
                    "completed_credits": completed,
                    "category": category,
                    "area": area,
                })
            else:
                is_fulfilled = completed >= required_credits
                missing_credits = max(0.0, required_credits - completed)

                analysis_result["requirements_analysis"].append({
                    "category": category,
                    "area": area,
                    "required_credits": required_credits,
                    "completed_credits": completed,
                    "missing_credits": missing_credits,
                    "is_fulfilled": is_fulfilled,
                    "completion_rate": round((completed / required_credits * 100), 2) if required_credits > 0 else 100,
                })

            if category == '교양':
                교양_이수합 += completed
                liberal_arts_detail[area if area else '기타'] = completed
            else:
                비교양_이수합 += completed

        # 개신기초교양 총합 판정 추가
        if gsin_basic_requirements:
            total_required = sum(r["required_credits"] for r in gsin_basic_requirements)
            total_completed = sum(r["completed_credits"] for r in gsin_basic_requirements)
            is_fulfilled = total_completed >= total_required
            missing_credits = max(0.0, total_required - total_completed)
            analysis_result["requirements_analysis"].append({
                "category": "교양",
                "area": "개신기초교양(총합)",
                "required_credits": total_required,
                "completed_credits": total_completed,
                "missing_credits": missing_credits,
                "is_fulfilled": is_fulfilled,
                "completion_rate": round((total_completed / total_required * 100), 2) if total_required > 0 else 100,
            })
            # 각 파트 개별 충족 정보도 함께 제공 (4개 파트 모두 포함)
            all_parts = ['인성과 비판적 사고', '의사소통', '영어', '정보문해']
            per_part_required = 3.0  # 각 파트는 3학점 고정
            analysis_result["gsin_basic_detail"] = {
                part: {
                    "completed_credits": round(gsin_parts_credits.get(part, 0.0), 2),
                    "required_credits": per_part_required,
                    "is_fulfilled": gsin_parts_credits.get(part, 0.0) >= per_part_required,
                    "missing_credits": max(0.0, per_part_required - gsin_parts_credits.get(part, 0.0))
                }
                for part in all_parts
            }

        # OCU기타 교양이 졸업요건에 없지만 이수학점이 있으면 추가 (프론트 표시 보장)
        ocu_key = '교양_OCU기타'
        if ocu_key in completed_credits_by_category:
            ocu_completed = float(completed_credits_by_category[ocu_key])
            # requirements_analysis에 OCU기타가 없으면 추가
            if not any(r.get('category') == '교양' and r.get('area') == 'OCU기타' for r in analysis_result["requirements_analysis"]):
                analysis_result["requirements_analysis"].append({
                    "category": "교양",
                    "area": "OCU기타",
                    "required_credits": 0.0,
                    "completed_credits": ocu_completed,
                    "missing_credits": 0.0,
                    "is_fulfilled": True,
                    "completion_rate": 100.0
                })
                liberal_arts_detail['OCU기타'] = ocu_completed

        # 일반선택(일선) 이수학점이 있으면 추가
        일선_key = '일선_일선'
        if general_elective > 0:
            # requirements_analysis에 일반선택이 없으면 추가
            if not any(r.get('category') == '일선' for r in analysis_result["requirements_analysis"]):
                analysis_result["requirements_analysis"].append({
                    "category": "일선",
                    "area": "일선",
                    "required_credits": 0.0,
                    "completed_credits": general_elective,
                    "missing_credits": 0.0,
                    "is_fulfilled": True,
                    "completion_rate": 100.0
                })
                비교양_이수합 += general_elective
        
        # 다전공 과목 처리 (course_records에서 category='다전공')
        다전공_이수학점 = float(completed_credits_by_category.get('다전공', 0.0)) + float(completed_credits_by_category.get('다전공_다전공', 0.0))
        if 다전공_이수학점 > 0:
            logger.info(f"다전공 과목 이수학점: {다전공_이수학점}학점")
            비교양_이수합 += 다전공_이수학점
            # requirements_analysis에 추가
            if not any(r.get('category') == '다전공' for r in analysis_result["requirements_analysis"]):
                analysis_result["requirements_analysis"].append({
                    "category": "다전공",
                    "area": "다전공",
                    "required_credits": 0.0,
                    "completed_credits": 다전공_이수학점,
                    "missing_credits": 0.0,
                    "is_fulfilled": True,
                    "completion_rate": 100.0
                })

        # 졸업요건에 없는 교양 하위영역(OCU/기타 등) 별도 집계
        for key, value in completed_credits_by_category.items():
            if key.startswith('교양_') and key not in 교양_요건_키:
                기타_교양_이수합 += value
                liberal_arts_detail[key.replace('교양_', '기타_')] = value

        # 영역 없는 교양 과목 처리 (키='교양' 단일)
        영역없는교양 = float(completed_credits_by_category.get('교양', 0.0))
        if 영역없는교양 > 0:
            logger.info(f"영역 분류 없는 교양 과목 학점: {영역없는교양}학점 - 요건표 영역에 분배 시도")
            parsing_warnings.append(f'영역 분류 없는 교양 {영역없는교양}학점을 자동 분배하였습니다.')
            # 요건 영역별로 부족분을 채우기
            for requirement in filtered_requirements:
                if requirement.get('category') == '교양' and 영역없는교양 > 0:
                    area = requirement.get('area', '')
                    required_credits = float(requirement.get('required_credits', 0))
                    key = f"교양_{area}" if area else '교양'
                    current_completed = float(completed_credits_by_category.get(key, 0.0))
                    if current_completed < required_credits:
                        shortage = required_credits - current_completed
                        fill_amount = min(shortage, 영역없는교양)
                        completed_credits_by_category[key] = current_completed + fill_amount
                        영역없는교양 -= fill_amount
                        logger.info(f"교양 영역 '{area}'에 {fill_amount}학점 분배 (required={required_credits}, was={current_completed})")
            # 남은 분량은 기타교양으로 처리
            if 영역없는교양 > 0:
                기타_교양_이수합 += 영역없는교양
                logger.info(f"남은 영역분류없는교양 {영역없는교양}학점을 기타교양으로 처리")
        
        # 교양 상한 적용 및 초과분 분리
        교양_총합 = 교양_이수합 + 기타_교양_이수합
        인정_교양_이수학점 = min(교양_총합, 교양_상한)
        교양_초과분 = max(0.0, 교양_총합 - 교양_상한)

        analysis_result["liberal_arts_detail"] = liberal_arts_detail
        analysis_result["liberal_arts_cap"] = 교양_상한
        analysis_result["liberal_arts_overflow"] = 교양_초과분

        # 전체 이수학점 = 비교양 이수합 + (상한 적용된 교양 이수학점)
        analysis_result["total_completed_credits"] = 비교양_이수합 + 인정_교양_이수학점

        # 필요학점 = 졸업이수학점(예: 130)
        analysis_result["total_required_credits"] = grad_total_credit
        if grad_total_credit > 0:
            analysis_result["overall_completion_rate"] = round(
                (analysis_result["total_completed_credits"] / grad_total_credit * 100), 2
            )

        # 미달 요건
        for req in analysis_result["requirements_analysis"]:
            if not req["is_fulfilled"]:
                analysis_result["missing_requirements"].append(req)

        curriculum = self.get_curriculum_courses(student_info.get('department'), admission_year)
        # 이미 이수한 과목 코드를 집계하여 추천에서 제외
        passed_codes = self._collect_passed_course_codes(adjusted_courses)
        analysis_result["recommendations"] = self._generate_recommendations(analysis_result["missing_requirements"], curriculum, passed_codes)
        self._save_analysis_result(student_id, analysis_result)
        return analysis_result

    def _apply_recognition_rules(self, courses: List[Dict], recognition: Dict[str, List[Dict]]) -> List[Dict]:
        if not recognition:
            return courses
        rules = recognition.get('rules', [])
        course_rules = recognition.get('courses', [])

        def recognizes_by_rule(c: Dict) -> bool:
            src_college = (c.get('area') or '').strip()  # 주의: area가 단과대 저장이 아닐 수 있음
            comp_type = (c.get('completion_type') or '').strip()
            # 규칙형: source_college 일치 + required_type_source가 전필이면 인정
            for r in rules:
                r_college = (r.get('source_college') or '').strip()
                r_required = (r.get('required_type_source') or '').strip()
                if r_college and r_required == '전필':
                    # 단과대 매핑은 course_records에 단과대가 없을 수 있어 코드로는 매칭이 어렵다.
                    # 보수적으로: 동일 단과대 정보가 없으면 규칙형은 건너뜀.
                    # 향후 과목 메타(단과대) 저장 시 정확 매칭 가능.
                    pass
            return False

        def recognizes_by_course(c: Dict) -> bool:
            code = (c.get('course_code') or '').strip()
            dept = (c.get('area') or '').strip()
            name = (c.get('course_name') or '').strip()
            for r in course_rules:
                if (r.get('course_code') or '').strip() == code:
                    return True
            return False

        adjusted = []
        for c in courses:
            cat = (c.get('category') or '').strip()
            # 이미 전공인 경우 그대로
            if cat == '전공':
                adjusted.append(c)
                continue
            # 개별과목 규칙에 해당하면 전선으로 변환
            if recognizes_by_course(c) or recognizes_by_rule(c):
                newc = dict(c)
                newc['category'] = '전공'
                newc['area'] = '전공선택'
                adjusted.append(newc)
            else:
                adjusted.append(c)
        return adjusted

    def _extract_admission_year(self, admission_date) -> int:
        if isinstance(admission_date, str):
            try:
                return int(admission_date[:4])
            except:
                pass
        elif hasattr(admission_date, 'year'):
            return admission_date.year
        return 2020

    def _calculate_completed_credits(self, courses: List[Dict]) -> Dict[str, float]:
        credits_by_category = {}
        for course in courses:
            if self._is_passed_course(course):
                category = course.get('category', '기타')
                area = course.get('area', '')
                key = f"{category}_{area}" if area else category
                credit = float(course.get('credit', 0))
                credits_by_category[key] = credits_by_category.get(key, 0.0) + credit
        return credits_by_category

    def _is_passed_course(self, course: Dict) -> bool:
        grade = str(course.get('grade', '')).upper() if course.get('grade') is not None else ''
        completion = str(course.get('completion_type', '')).upper() if course.get('completion_type') is not None else ''
        # 통과로 인정하는 코드들 (성적/이수구분 모두 포함)
        passing_grades = {'A+', 'A0', 'A-', 'B+', 'B0', 'B-', 'C+', 'C0', 'C-', 'D+', 'D0', 'P', 'PASS', '통과', '이수', '합격'}
        if grade in passing_grades:
            return True
        if completion in passing_grades:
            return True
        
        # 페일세이프: completion_type이 카테고리명('교양', '전공', '일선' 등)이면 학점>0 시 통과
        category_keywords = {'교양', '전공', '일선', '일반선택', '전공필수', '전공선택', '일반교양', '확대교양'}
        if any(kw in completion for kw in category_keywords):
            try:
                credit = float(course.get('credit', 0))
                if credit > 0:
                    return True
            except:
                pass
        
        # 페일세이프: 성적/이수구분 모두 없으면 학점>0 시 임시 통과 처리
        if not grade and not completion:
            try:
                credit = float(course.get('credit', 0))
                if credit > 0:
                    return True
            except:
                pass
        return False

    def _analyze_category_requirement(self, requirement: Dict, courses: List[Dict], completed_credits: Dict) -> Dict:
        category = requirement.get('category')
        area = requirement.get('area', '')
        required_credits = float(requirement.get('required_credits', 0))
        key = f"{category}_{area}" if area else category
        completed_credits_in_category = float(completed_credits.get(key, 0.0))

        is_fulfilled = completed_credits_in_category >= required_credits
        missing_credits = max(0.0, required_credits - completed_credits_in_category)

        relevant_courses = [
            course for course in courses
            if course.get('category') == category and (not area or course.get('area') == area)
            and self._is_passed_course(course)
        ]

        return {
            "category": category,
            "area": area,
            "required_credits": required_credits,
            "completed_credits": completed_credits_in_category,
            "missing_credits": missing_credits,
            "is_fulfilled": is_fulfilled,
            "completion_rate": round((completed_credits_in_category / required_credits * 100), 2) if required_credits > 0 else 100,
            "relevant_courses": relevant_courses
        }

    def _generate_recommendations(self, missing_requirements: List[Dict], curriculum: List[Dict], passed_codes: set) -> List[str]:
        recommendations = []
        if not missing_requirements:
            return ["모든 졸업 요건을 충족하였습니다."]

        # 간단 규칙:
        # - 전공필수 부족: curriculum.required_type='전필' 과목 추천
        # - 전공선택 부족: curriculum.required_type='전선' 과목 추천
        # - 교양/일선은 과목 추천은 생략(학과 외 범위 다양성)
        # 추천은 grade_year/term 오름차순 정렬 기준 상위 3개 표시
        by_type = {
            '전필': [c for c in curriculum if c.get('required_type') == '전필' and (c.get('course_code') or '').strip() not in passed_codes],
            '전선': [c for c in curriculum if c.get('required_type') == '전선' and (c.get('course_code') or '').strip() not in passed_codes]
        }

        missing_requirements.sort(key=lambda x: x['missing_credits'], reverse=True)
        for req in missing_requirements:
            cat = req.get('category')
            area = req.get('area')
            miss = float(req.get('missing_credits', 0) or 0)
            if miss <= 0:
                continue
            if cat == '전공' and area == '전공필수':
                pool = by_type['전필'][:]
                # 전필은 개수 제한 없이 모두 추천
                picks = pool
                if picks:
                    rec_list = ', '.join(f"{p.get('grade_year', '?')}학년|{p['course_name']}" for p in picks)
                    recommendations.append(f"전공필수 {miss}학점 부족: 권장 과목 → {rec_list}")
                else:
                    recommendations.append(f"전공필수 {miss}학점 부족: 커리큘럼 과목 목록 없음")
            elif cat == '전공' and area == '전공선택':
                pool = by_type['전선'][:]
                # 전선은 최대 8개 추천
                picks = pool[:8]
                if picks:
                    rec_list = ', '.join(f"{p.get('grade_year', '?')}학년|{p['course_name']}" for p in picks)
                    recommendations.append(f"전공선택 {miss}학점 부족: 추천 과목 → {rec_list}")
                else:
                    recommendations.append(f"전공선택 {miss}학점 부족: 커리큘럼 과목 목록 없음")
            else:
                recommendations.append(f"{cat} {area} {miss}학점 부족")

        total_missing = sum(float(req['missing_credits']) for req in missing_requirements)
        if total_missing > 0:
            recommendations.append(f"졸업까지 총 {total_missing}학점이 부족합니다.")
        return recommendations

    def _collect_passed_course_codes(self, courses: List[Dict]) -> set:
        codes = set()
        for c in courses:
            try:
                if self._is_passed_course(c):
                    code = (c.get('course_code') or '').strip()
                    if code:
                        codes.add(code)
            except Exception:
                continue
        return codes

    def _save_analysis_result(self, student_id: str, analysis_result: Dict):
        try:
            cursor = self.connection.cursor()
            query = """
            INSERT INTO graduation_analysis (
                student_id, analysis_date, total_completed_credits,
                total_required_credits, overall_completion_rate,
                analysis_result, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE
                analysis_date = VALUES(analysis_date),
                total_completed_credits = VALUES(total_completed_credits),
                total_required_credits = VALUES(total_required_credits),
                overall_completion_rate = VALUES(overall_completion_rate),
                analysis_result = VALUES(analysis_result),
                updated_at = NOW()
            """
            values = (
                student_id,
                analysis_result["analysis_date"],
                float(analysis_result["total_completed_credits"]),
                float(analysis_result["total_required_credits"]),
                float(analysis_result["overall_completion_rate"]),
                json.dumps(analysis_result, ensure_ascii=False, default=str)
            )
            cursor.execute(query, values)
            self.connection.commit()
            cursor.close()
            logger.info(f"학번 {student_id} 분석 결과 저장 완료")
        except Error as e:
            logger.error(f"분석 결과 저장 오류: {e}")
            self.connection.rollback()

    def get_saved_analysis(self, student_id: str) -> Optional[Dict]:
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT * FROM graduation_analysis 
            WHERE student_id = %s 
            ORDER BY analysis_date DESC 
            LIMIT 1
            """
            cursor.execute(query, (student_id,))
            result = cursor.fetchone()
            cursor.close()
            if result and result.get('analysis_result'):
                return json.loads(result['analysis_result'])
            return None
        except Error as e:
            logger.error(f"저장된 분석 결과 조회 오류: {e}")
            return None

def analyze_student_graduation(student_id: str, db_config: Dict[str, str], parsing_warnings: Optional[List[str]] = None) -> Dict:
    checker = GraduationRequirementsChecker(db_config)
    try:
        checker.connect_db()
        return checker.analyze_graduation_status(student_id, parsing_warnings)
    except Exception as e:
        logger.error(f"졸업 요건 분석 중 오류 발생: {e}")
        return {"error": str(e)}
    finally:
        checker.disconnect_db()

if __name__ == "__main__":
    db_config = {
        'host': '203.255.78.58',
        'port': 9003,
        'database': 'graduation_system',
        'user': 'user29',
        'password': '123'
    }
    test_student_id = '2023001'
    result = analyze_student_graduation(test_student_id, db_config)
    if 'error' not in result:
        print(f"분석 완료: 전체 이수율 {result['overall_completion_rate']}%")
    else:
        print(f"분석 실패: {result['error']}")
