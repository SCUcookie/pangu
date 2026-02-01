"""
数据加载器 - AgentV2
支持不同格式的EduBench数据集加载
"""
import json
import os
import glob
from typing import List, Dict, Any, Optional
from config import (
    ZH_DATA_DIR, EN_DATA_DIR, TASK_TYPES, 
    DEBUG_MODE, DEBUG_SAMPLE_SIZE
)


class DataItem:
    """统一的数据项结构"""
    def __init__(
        self,
        task_type: str,
        prompt: str,
        question: str,
        answer: Any = None,
        subject: str = "",
        education_level: str = "",
        question_type: str = "",
        lang: str = "zh",
        raw_data: Dict = None,
        source_file: str = ""
    ):
        self.task_type = task_type
        self.prompt = prompt
        self.question = question
        self.answer = answer
        self.subject = subject
        self.education_level = education_level
        self.question_type = question_type
        self.lang = lang
        self.raw_data = raw_data or {}
        self.source_file = source_file
    
    def to_dict(self) -> Dict:
        return {
            "task_type": self.task_type,
            "prompt": self.prompt,
            "question": self.question,
            "answer": self.answer,
            "subject": self.subject,
            "education_level": self.education_level,
            "question_type": self.question_type,
            "lang": self.lang,
            "source_file": self.source_file
        }


class DataLoader:
    """数据加载器，支持多种jsonl格式"""
    
    def __init__(self, zh_data_dir: str = ZH_DATA_DIR, en_data_dir: str = EN_DATA_DIR):
        self.zh_data_dir = zh_data_dir
        self.en_data_dir = en_data_dir
        
    def load_all(self) -> List[DataItem]:
        """加载所有数据"""
        all_data = []
        
        # 加载中文数据
        zh_files = glob.glob(os.path.join(self.zh_data_dir, "*.jsonl"))
        for file_path in zh_files:
            data = self._load_file(file_path, lang="zh")
            all_data.extend(data)
            print(f"Loaded {len(data)} items from {os.path.basename(file_path)} (zh)")
        
        # 加载英文数据
        en_files = glob.glob(os.path.join(self.en_data_dir, "*.jsonl"))
        for file_path in en_files:
            data = self._load_file(file_path, lang="en")
            all_data.extend(data)
            print(f"Loaded {len(data)} items from {os.path.basename(file_path)} (en)")
        
        print(f"Total loaded: {len(all_data)} items")
        return all_data
    
    def load_by_task(self, task_type: str) -> List[DataItem]:
        """按任务类型加载数据"""
        all_data = []
        filename = f"{task_type}.jsonl"
        
        zh_file = os.path.join(self.zh_data_dir, filename)
        if os.path.exists(zh_file):
            all_data.extend(self._load_file(zh_file, lang="zh"))
        
        en_file = os.path.join(self.en_data_dir, filename)
        if os.path.exists(en_file):
            all_data.extend(self._load_file(en_file, lang="en"))
        
        return all_data
    
    def _load_file(self, file_path: str, lang: str) -> List[DataItem]:
        """加载单个jsonl文件"""
        filename = os.path.basename(file_path)
        task_key = filename.replace(".jsonl", "").replace(".py", "")
        task_type = TASK_TYPES.get(task_key, task_key)
        
        items = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f):
                    if not line.strip():
                        continue
                    try:
                        raw = json.loads(line)
                        item = self._parse_item(raw, task_type, lang, filename)
                        if item:
                            items.append(item)
                            
                        # 调试模式下限制数量
                        if DEBUG_MODE and len(items) >= DEBUG_SAMPLE_SIZE:
                            break
                            
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error in {filename} line {line_num}: {e}")
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
        
        return items
    
    def _parse_item(self, raw: Dict, task_type: str, lang: str, source_file: str) -> Optional[DataItem]:
        """根据任务类型解析数据项"""
        
        # 通用字段提取
        subject = raw.get("学科", raw.get("Subject", ""))
        education_level = raw.get("学制级别", raw.get("难度", raw.get("Education Level", "")))
        question_type = raw.get("题型", raw.get("Question Type", ""))
        
        # 根据任务类型解析
        if task_type == "question_answering":
            return self._parse_qa(raw, task_type, lang, source_file, subject, education_level, question_type)
        elif task_type == "automatic_grading":
            return self._parse_grading(raw, task_type, lang, source_file, subject, education_level, question_type)
        elif task_type == "error_correction":
            return self._parse_error_correction(raw, task_type, lang, source_file, subject, education_level, question_type)
        elif task_type == "idea_prompting":
            return self._parse_idea_prompting(raw, task_type, lang, source_file, subject, education_level, question_type)
        elif task_type == "personalized_content":
            return self._parse_personalized_content(raw, task_type, lang, source_file, subject, education_level, question_type)
        elif task_type == "personalized_learning":
            return self._parse_personalized_learning(raw, task_type, lang, source_file, subject, education_level, question_type)
        elif task_type == "question_generation":
            return self._parse_question_generation(raw, task_type, lang, source_file, subject, education_level, question_type)
        elif task_type == "teaching_material":
            return self._parse_teaching_material(raw, task_type, lang, source_file, subject, education_level, question_type)
        else:
            # 默认解析
            return self._parse_default(raw, task_type, lang, source_file, subject, education_level, question_type)
    
    def _parse_qa(self, raw: Dict, task_type: str, lang: str, source_file: str, 
                  subject: str, education_level: str, question_type: str) -> DataItem:
        """解析问答类型数据"""
        question = raw.get("问题", raw.get("Question", raw.get("question", "")))
        answer = raw.get("答案", raw.get("Answer", ""))
        prompt = raw.get("prompt", question)
        
        return DataItem(
            task_type=task_type,
            prompt=prompt,
            question=question,
            answer=answer,
            subject=subject,
            education_level=education_level,
            question_type=question_type,
            lang=lang,
            raw_data=raw,
            source_file=source_file
        )
    
    def _parse_grading(self, raw: Dict, task_type: str, lang: str, source_file: str,
                       subject: str, education_level: str, question_type: str) -> DataItem:
        """解析自动评分类型数据"""
        question_info = raw.get("问题", {})
        if isinstance(question_info, dict):
            question = question_info.get("题目", "") + "\n" + str(question_info.get("选项", []))
        else:
            question = str(question_info)
        
        student_answer = raw.get("学生的答案", "")
        expected_score = raw.get("评分", "")
        score_detail = raw.get("评分细节", "")
        feedback = raw.get("个性化反馈", "")
        
        prompt = raw.get("question", f"题目：{question}\n学生答案：{student_answer}\n请给出评分和反馈。")
        
        return DataItem(
            task_type=task_type,
            prompt=prompt,
            question=question,
            answer={"score": expected_score, "detail": score_detail, "feedback": feedback},
            subject=subject,
            education_level=education_level,
            question_type=question_type,
            lang=lang,
            raw_data=raw,
            source_file=source_file
        )
    
    def _parse_error_correction(self, raw: Dict, task_type: str, lang: str, source_file: str,
                                 subject: str, education_level: str, question_type: str) -> DataItem:
        """解析纠错类型数据"""
        question = raw.get("问题", raw.get("question", ""))
        original_answer = raw.get("原答案", [])
        corrected_answer = raw.get("纠错后答案", [])
        correction_note = raw.get("纠错说明", "")
        
        prompt = raw.get("question", question)
        
        return DataItem(
            task_type=task_type,
            prompt=prompt,
            question=question,
            answer={"original": original_answer, "corrected": corrected_answer, "note": correction_note},
            subject=subject,
            education_level=education_level,
            question_type=question_type,
            lang=lang,
            raw_data=raw,
            source_file=source_file
        )
    
    def _parse_idea_prompting(self, raw: Dict, task_type: str, lang: str, source_file: str,
                               subject: str, education_level: str, question_type: str) -> DataItem:
        """解析思路提示类型数据"""
        question = raw.get("问题", raw.get("question", ""))
        provided_idea = raw.get("提供的思路", "")
        
        prompt = raw.get("question", question)
        
        return DataItem(
            task_type=task_type,
            prompt=prompt,
            question=question,
            answer=provided_idea,
            subject=subject,
            education_level=education_level,
            question_type=question_type,
            lang=lang,
            raw_data=raw,
            source_file=source_file
        )
    
    def _parse_personalized_content(self, raw: Dict, task_type: str, lang: str, source_file: str,
                                     subject: str, education_level: str, question_type: str) -> DataItem:
        """解析个性化学习内容类型数据"""
        student_profile = raw.get("学生画像", raw.get("学生的画像", {}))
        learning_path = raw.get("学习路径规划建议", [])
        personalized_content = raw.get("个性化意见生成", {})
        
        prompt = raw.get("question", str(student_profile))
        
        return DataItem(
            task_type=task_type,
            prompt=prompt,
            question=str(student_profile),
            answer={"path": learning_path, "content": personalized_content},
            subject=subject,
            education_level=education_level,
            question_type=question_type,
            lang=lang,
            raw_data=raw,
            source_file=source_file
        )
    
    def _parse_personalized_learning(self, raw: Dict, task_type: str, lang: str, source_file: str,
                                      subject: str, education_level: str, question_type: str) -> DataItem:
        """解析个性化学习方案类型数据"""
        student_profile = raw.get("学生的画像", {})
        learning_content = raw.get("个性化学习内容/任务", {})
        
        prompt = raw.get("question", str(student_profile))
        
        return DataItem(
            task_type=task_type,
            prompt=prompt,
            question=str(student_profile),
            answer=learning_content,
            subject=subject,
            education_level=education_level,
            question_type=question_type,
            lang=lang,
            raw_data=raw,
            source_file=source_file
        )
    
    def _parse_question_generation(self, raw: Dict, task_type: str, lang: str, source_file: str,
                                    subject: str, education_level: str, question_type: str) -> DataItem:
        """解析题目生成类型数据"""
        knowledge_point = raw.get("知识点", "")
        generated_question = raw.get("问题", "")
        generated_idea = raw.get("提供的思路", "")
        generated_answer = raw.get("答案", "")
        
        prompt = raw.get("question", f"知识点：{knowledge_point}")
        
        return DataItem(
            task_type=task_type,
            prompt=prompt,
            question=knowledge_point,
            answer={"question": generated_question, "idea": generated_idea, "answer": generated_answer},
            subject=subject,
            education_level=education_level,
            question_type=question_type,
            lang=lang,
            raw_data=raw,
            source_file=source_file
        )
    
    def _parse_teaching_material(self, raw: Dict, task_type: str, lang: str, source_file: str,
                                  subject: str, education_level: str, question_type: str) -> DataItem:
        """解析教学素材生成类型数据"""
        knowledge_point = raw.get("知识点", "")
        teaching_material = raw.get("教学素材", {})
        
        prompt = raw.get("question", f"知识点：{knowledge_point}")
        
        return DataItem(
            task_type=task_type,
            prompt=prompt,
            question=knowledge_point,
            answer=teaching_material,
            subject=subject,
            education_level=education_level,
            question_type=question_type,
            lang=lang,
            raw_data=raw,
            source_file=source_file
        )
    
    def _parse_default(self, raw: Dict, task_type: str, lang: str, source_file: str,
                       subject: str, education_level: str, question_type: str) -> DataItem:
        """默认解析方法"""
        question = raw.get("question", raw.get("问题", ""))
        answer = raw.get("answer", raw.get("答案", ""))
        prompt = raw.get("prompt", question)
        
        return DataItem(
            task_type=task_type,
            prompt=prompt,
            question=question,
            answer=answer,
            subject=subject,
            education_level=education_level,
            question_type=question_type,
            lang=lang,
            raw_data=raw,
            source_file=source_file
        )


if __name__ == "__main__":
    # 测试数据加载器
    loader = DataLoader()
    data = loader.load_all()
    
    # 按任务类型统计
    task_counts = {}
    for item in data:
        task_counts[item.task_type] = task_counts.get(item.task_type, 0) + 1
    
    print("\nTask type distribution:")
    for task, count in sorted(task_counts.items()):
        print(f"  {task}: {count}")
