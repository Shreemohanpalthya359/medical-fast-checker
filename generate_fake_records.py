from fpdf import FPDF
import os

def create_pdf(filename, title, patient_info, report_content, conclusion):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, title, new_x='LMARGIN', new_y='NEXT', align='C')
    pdf.ln(5)
    
    # Patient Info
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 10, 'Patient Information', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 11)
    for key, value in patient_info.items():
        pdf.cell(0, 8, f"{key}: {value}", new_x='LMARGIN', new_y='NEXT')
    pdf.ln(5)
    
    # Clinical Findings
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 10, 'Clinical Findings & Laboratory Results', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 11)
    pdf.multi_cell(0, 8, report_content)
    pdf.ln(5)
    
    # Conclusion
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 10, 'Diagnostic Conclusion', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 11)
    pdf.multi_cell(0, 8, conclusion)
    
    pdf.output(filename)
    print(f"Generated {filename}")

if __name__ == '__main__':
    os.makedirs('test_records', exist_ok=True)
    
    # Record 1: Cardiology
    create_pdf(
        'test_records/Cardiology_Report_JohnDoe.pdf',
        'CARDIOLOGY CONSULTATION REPORT',
        {
            'Patient Name': 'John Doe',
            'Age': '58',
            'Gender': 'Male',
            'Date of Examination': '2023-10-15',
            'Referring Physician': 'Dr. Sarah Jenkins'
        },
        "Patient presents with a 2-week history of exertional dyspnea and intermittent diaphoresis. No typical angina pectoris, but reports vague retrosternal discomfort during heavy listing. \n\nECG reveals sinus rhythm at 78 bpm, with isolated premature ventricular complexes (PVCs) and nonspecific ST-T wave abnormalities in the inferior leads (II, III, aVF).\n\nEchocardiogram shows a preserved left ventricular ejection fraction (LVEF) of 55%. Mild concentric left ventricular hypertrophy is noted. There is mild-to-moderate mitral regurgitation, structurally normal aortic valve.",
        "1. Essential hypertension with secondary mild left ventricular hypertrophy.\n2. Mild-to-moderate mitral regurgitation, likely secondary to annular geometry changes.\n3. Atypical chest pain, low clinical probability for acute coronary syndrome. Recommend outpatient stress echocardiography to completely rule out inducible ischemia. Start on low-dose beta-blocker therapy (Metoprolol 25mg daily) for PVC suppression and BP control."
    )

    # Record 2: Oncology / Hematology
    create_pdf(
        'test_records/Hematology_Report_JaneSmith.pdf',
        'HEMATOLOGY & ONCOLOGY LAB RESULTS',
        {
            'Patient Name': 'Jane Smith',
            'Age': '42',
            'Gender': 'Female',
            'Date of Examination': '2023-11-02',
            'Attending': 'Dr. Robert Chen'
        },
        "Complete Blood Count (CBC) Panel:\n- Hemoglobin (Hb): 9.2 g/dL (Low, Reference: 12.0-15.5 g/dL)\n- Hematocrit (Hct): 28% (Low, Reference: 37-48%)\n- Mean Corpuscular Volume (MCV): 72 fL (Low, Reference: 80-100 fL)\n- Platelet Count: 450,000 /mcL (Elevated)\n- White Blood Cell (WBC) Count: 8,400 /mcL (Normal)\n\nIron Studies:\n- Serum Iron: 35 mcg/dL (Low)\n- Total Iron Binding Capacity (TIBC): 480 mcg/dL (Elevated)\n- Ferritin: 8 ng/mL (Significantly Low, Reference: 15-150 ng/mL)\n\nPeripheral Blood Smear: Microcytic, hypochromic red blood cells with marked anisocytosis and pencil cells.",
        "Severe iron deficiency anemia, likely secondary to chronic blood loss (evaluate gynecological and gastrointestinal sources). The elevated platelet count is consistent with reactive thrombocytosis due to severe iron depletion. No blast cells or signs of primary hematological malignancy observed.\n\nPlan: Initiate oral elemental iron supplementation (ferrous sulfate 325 mg orally every other day) and refer to gastroenterology for bidirectional endoscopy. Monitor CBC in 4 weeks."
    )
    
    # Record 3: Neurology Extract
    create_pdf(
        'test_records/Neurology_Extract_Test.pdf',
        'NEUROLOGICAL EVALUATION SUMMARY',
        {
            'Patient Name': 'Alan Turing (Dummy Data)',
            'Age': '65',
            'Date': '2024-01-20'
        },
        "Patient exhibits resting tremor predominantly in the right upper extremity, characterized by a 'pill-rolling' motion at 4-6 Hz. Tremor decreases with voluntary movement. Bradykinesia is evident during fast alternating hand movements and finger tapping bilaterally, but worse on the right. Rigidity detected in the right wrist (cogwheel type).\n\nGait analysis shows decreased arm swing on the right, stooped posture, and slight shuffling. Postural reflexes are mildly impaired (retropulsion test 1-2 steps back but recovers independently). Cognition is intact (MoCA score 28/30). No gaze palsies.",
        "Clinical presentation is highly characteristic of idiopathic Parkinson's disease (Hoehn and Yahr Stage 2). \n\nRecommendation: Initiate trial of Carbidopa/Levodopa 25/100 mg half-tablet three times daily with meals. Follow up in 6 weeks to assess motor response and titrate accordingly. Provide education regarding disease progression."
    )
