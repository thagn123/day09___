import json
import os
from pathlib import Path
from datetime import datetime
from rag_answer import rag_answer
from eval import VARIANT_CONFIG

# Gợi ý từ file SCORING.md để nhóm thi nộp bài
GRADING_FILE = Path("data/grading_questions.json")
LOG_DIR = Path("logs")

def main():
    if not GRADING_FILE.exists():
        print(f"Lỗi: Không tìm thấy file {GRADING_FILE}. (File này sẽ được public lúc 17:00)")
        return
        
    with open(GRADING_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)

    log = []
    
    # Sử dụng config tốt nhất mà nhóm đã chọn ở Sprint 3 -> Variant Config
    print(f"Bắt đầu chạy Grading với {len(questions)} câu hỏi ẩn...")
    
    for q in questions:
        print(f"  Đang chạy câu hỏi: [{q['id']}] {q['question']}")
        try:
            result = rag_answer(
                q["question"], 
                retrieval_mode=VARIANT_CONFIG.get("retrieval_mode", "hybrid"), 
                verbose=False
            )
            log.append({
                "id": q["id"],
                "question": q["question"],
                "answer": result["answer"],
                "sources": result["sources"],
                "chunks_retrieved": len(result["chunks_used"]),
                "retrieval_mode": result["config"]["retrieval_mode"],
                "timestamp": datetime.now().isoformat(),
            })
        except Exception as e:
            print(f"Lỗi khi chạy câu {q['id']}: {e}")
            log.append({
                "id": q["id"],
                "answer": f"PIPELINE_ERROR: {e}",
                "timestamp": datetime.now().isoformat()
            })

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    out_file = LOG_DIR / "grading_run.json"
    
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
        
    print(f"\nHoàn tất! Kết quả đã được lưu tại: {out_file}")

if __name__ == "__main__":
    main()
