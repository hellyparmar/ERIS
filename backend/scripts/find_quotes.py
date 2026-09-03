with open('backend/app/routers/causal_analysis.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if '\"\"\"' in line:
            print(f"{i+1}: {line.strip()}")
