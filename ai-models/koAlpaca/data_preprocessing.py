import json
import random
import re
from jamo import hangul_to_jamo, jamo_to_hangul

# 비슷한 자음, 모음
similar_consonants = { ... }  # 생략
similar_vowels = { ... }  # 생략

# ✅ 자모(ㄱ~ㅎ, ㅏ~ㅣ) 제거 함수
def clean_text(text):
    jamo_pattern = re.compile(r'[\u3131-\u3163]+')
    cleaned = jamo_pattern.sub('', text).strip()
    return cleaned

# ✅ 한글인지 확인
def is_hangul_char(c):
    return '가' <= c <= '힣'

# 후보 보기 생성
def perturb_korean_word(word):
    candidates = set()
    for _ in range(20):
        try:
            jamo_list = list(hangul_to_jamo(word))
        except Exception:
            continue

        i = random.randint(0, len(jamo_list) - 1)
        c = jamo_list[i]

        if c in similar_consonants:
            jamo_list[i] = random.choice(similar_consonants[c])
        elif c in similar_vowels:
            jamo_list[i] = random.choice(similar_vowels[c])
        else:
            continue

        try:
            perturbed = jamo_to_hangul(''.join(jamo_list))
            if perturbed != word and all(is_hangul_char(ch) for ch in perturbed if ch.isalpha()):
                candidates.add(perturbed)
        except:
            continue

        if len(candidates) >= 3:
            break
    return list(candidates)

# ✅ 맞춤법 문제
def load_spelling_data(path, limit=100):
    with open(path, 'r', encoding='utf-8') as f:
        spelling_raw = json.load(f)

    problems = []
    count = 0
    for doc in spelling_raw['document']:
        for utt in doc.get("utterance", []):
            original = clean_text(utt.get("original_form", ""))
            corrected = clean_text(utt.get("corrected_form", ""))
            if not original or not corrected or original == corrected:
                continue
            if original not in corrected:
                continue

            input_text = corrected.replace(original, "_____")

            wrong_choices = perturb_korean_word(original)
            if len(wrong_choices) == 3:
                choices = wrong_choices + [original]
                random.shuffle(choices)
                problems.append({
                    "instruction": "다음 중 옳은 맞춤법은?",
                    "input": None,
                    "output": corrected,
                    "choices": choices
                })
                count += 1
                if count >= limit:
                    return problems
    return problems

# ✅ 외래어 문제
def load_foreign_data(path, limit=100):
    with open(path, 'r', encoding='utf-8') as f:
        foreign_words = json.load(f)

    problems = []
    count = 0
    for word in foreign_words:
        original = word.get("original", "").strip()
        korean = clean_text(word.get("korean", "").strip())

        if not original or not korean or len(korean) < 2:
            continue

        wrong_choices = perturb_korean_word(korean)
        if len(wrong_choices) == 3:
            choices = wrong_choices + [korean]
            random.shuffle(choices)
            problems.append({
                "instruction": "다음 원어 표기를 우리말로 옮기면?",
                "input": original,
                "output": korean,
                "choices": choices
            })
            count += 1

        if count >= limit:
            break

    return problems

# ✅ 사자성어 문제는 그대로
def load_idiom_data(*paths):
    problems = []
    all_idioms = []
    for path in paths:
        with open(path, 'r', encoding='utf-8') as f:
            idioms = json.load(f)
            all_idioms.extend(list(idioms.values()))
    for entry in all_idioms:
        question = entry.get("mean", "")
        answer = entry.get("korean_word", "")
        if question and answer:
            wrong_choices = [e["korean_word"] for e in random.sample(all_idioms, 10) if e["korean_word"] != answer]
            choices = random.sample(wrong_choices, 3) + [answer]
            random.shuffle(choices)
            problems.append({
                "instruction": "다음 뜻을 가진 사자성어는?",
                "input": question,
                "output": answer,
                "choices": choices
            })
    return problems

# ✅ 전체 데이터셋 생성
def create_dataset():
    spelling_limit = 100
    idiom_limit = 100
    foreign_limit = 100

    spelling = load_spelling_data("spelling.json", limit=spelling_limit)
    idioms = load_idiom_data("lionised_language1.json", "lionised_language2.json")[:idiom_limit]
    foreign = load_foreign_data("foreign_words_general.json", limit=foreign_limit)

    def split_data(data, ratio=0.8):
        split_idx = int(len(data) * ratio)
        return data[:split_idx], data[split_idx:]

    spelling_train, spelling_test = split_data(spelling)
    idioms_train, idioms_test = split_data(idioms)
    foreign_train, foreign_test = split_data(foreign)

    train_data = spelling_train + idioms_train + foreign_train
    test_data = spelling_test + idioms_test + foreign_test

    random.shuffle(train_data)
    random.shuffle(test_data)

    with open("train_dataset.json", "w", encoding="utf-8") as f:
        json.dump(train_data, f, ensure_ascii=False, indent=2)
    with open("test_dataset.json", "w", encoding="utf-8") as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 훈련 데이터: {len(train_data)}개, 테스트 데이터: {len(test_data)}개 생성 완료!")

# 실행
create_dataset()


# === 외래어 문제 생성 ===
def load_foreign_data(path, limit=100):
    with open(path, 'r', encoding='utf-8') as f:
        foreign_words = json.load(f)

    problems = []
    count = 0
    for word in foreign_words:
        original = word.get("original", "").strip()
        korean = word.get("korean", "").strip()

        # 빈 값이나 비정상적인 길이 건너뛰기
        if not original or not korean or len(korean) < 2:
            continue

        # 보기 후보 생성
        wrong_choices = perturb_korean_word(korean)

        # 유효한 보기 3개가 있을 때만 문제 생성
        if len(wrong_choices) == 3:
            choices = wrong_choices + [korean]
            random.shuffle(choices)
            problems.append({
                "instruction": "다음 원어 표기를 우리말로 옮기면?",
                "input": original,
                "output": korean,
                "choices": choices
            })
            count += 1

        if count >= limit:
            break

    return problems


# === 사자성어 문제 생성 ===
def load_idiom_data(*paths):
    problems = []
    all_idioms = []
    for path in paths:
        with open(path, 'r', encoding='utf-8') as f:
            idioms = json.load(f)
            all_idioms.extend(list(idioms.values()))
    for entry in all_idioms:
        question = entry.get("mean", "")
        answer = entry.get("korean_word", "")
        if question and answer:
            wrong_choices = [e["korean_word"] for e in random.sample(all_idioms, 10) if e["korean_word"] != answer]
            choices = random.sample(wrong_choices, 3) + [answer]
            random.shuffle(choices)
            problems.append({
                "instruction": "다음 뜻을 가진 사자성어는?",
                "input": question,
                "output": answer,
                "choices": choices
            })
    return problems

# === 데이터셋 생성 ===
def create_dataset():
    # 각 유형별로 문제 수 설정
    spelling_limit = 100
    idiom_limit = 100
    foreign_limit = 100

    # 데이터 로드
    spelling = load_spelling_data("spelling.json", limit=spelling_limit)
    idioms = load_idiom_data("lionised_language1.json", "lionised_language2.json")[:idiom_limit]
    foreign = load_foreign_data("foreign_words_general.json", limit=foreign_limit)

    # 각 유형별로 train/test 분할
    def split_data(data, ratio=0.8):
        split_idx = int(len(data) * ratio)
        return data[:split_idx], data[split_idx:]

    spelling_train, spelling_test = split_data(spelling)
    idioms_train, idioms_test = split_data(idioms)
    foreign_train, foreign_test = split_data(foreign)

    # 합치기
    train_data = spelling_train + idioms_train + foreign_train
    test_data = spelling_test + idioms_test + foreign_test

    # 셔플
    random.shuffle(train_data)
    random.shuffle(test_data)

    # 저장
    with open("train_dataset.json", "w", encoding="utf-8") as f:
        json.dump(train_data, f, ensure_ascii=False, indent=2)

    with open("test_dataset.json", "w", encoding="utf-8") as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)

    print(f"훈련 데이터: {len(train_data)}개, 테스트 데이터: {len(test_data)}개 생성 완료.")

# 실행
create_dataset()





##########################
# import json
# import random
#
# # === 1. 맞춤법 문제 생성 (빈칸 방식) ===
# def load_spelling_data(path):
#     with open(path, 'r', encoding='utf-8') as f:
#         spelling_raw = json.load(f)
#     problems = []
#     for doc in spelling_raw['document']:
#         for utt in doc.get("utterance", []):
#             original = utt.get("original_form")
#             corrected = utt.get("corrected_form")
#             if original != corrected and corrected and original in corrected:
#                 # corrected 문장에서 original 부분만 ()로 대체
#                 input_text = corrected.replace(original, "()")
#                 problem = {
#                     "instruction": "다음 중 빈칸에 들어갈 맞춤법으로 옳은 것은?",
#                     "input": input_text,
#                     "output": original
#                 }
#                 problems.append(problem)
#     return problems
#
# # === 2. 사자성어 문제 생성 ===
# def load_idiom_data(*paths):
#     problems = []
#     for path in paths:
#         with open(path, 'r', encoding='utf-8') as f:
#             idioms = json.load(f)
#         for entry in idioms.values():
#             question = entry.get("mean", "")
#             answer = entry.get("korean_word", "")
#             if question and answer:
#                 problems.append({
#                     "instruction": "다음 뜻을 가진 사자성어는?",
#                     "input": question,
#                     "output": answer
#                 })
#     return problems
#
# # === 3. 외래어 문제 생성 ===
# def load_foreign_data(path):
#     with open(path, 'r', encoding='utf-8') as f:
#         foreign_words = json.load(f)
#     problems = []
#     for word in foreign_words:
#         original = word["original"]
#         korean = word["korean"]
#         problems.append({
#             "instruction": "다음 원어 표기를 우리말로 옮기면?",
#             "input": original,
#             "output": korean
#         })
#     return problems
#
# # === 4. 통합 및 분할 저장 ===
# def create_dataset():
#     spelling = load_spelling_data("spelling.json")[:100]  # 필요시 개수 조절
#     idioms = load_idiom_data("lionised_language1.json", "lionised_language2.json")
#     foreign = load_foreign_data("foreign_words_general.json")[:100]
#
#     # 통합 및 셔플
#     full_data = spelling + idioms + foreign
#     random.shuffle(full_data)
#
#     # 80% 학습 / 20% 테스트 분할
#     split_idx = int(len(full_data) * 0.8)
#     train_data = full_data[:split_idx]
#     test_data = full_data[split_idx:]
#
#     with open("train_dataset.json", "w", encoding="utf-8") as f:
#         json.dump(train_data, f, ensure_ascii=False, indent=2)
#
#     with open("test_dataset.json", "w", encoding="utf-8") as f:
#         json.dump(test_data, f, ensure_ascii=False, indent=2)
#
#     print(f"총 {len(full_data)}개 중 {len(train_data)}개는 훈련용, {len(test_data)}개는 테스트용으로 저장됨.")
#
# # 실행
# create_dataset()
