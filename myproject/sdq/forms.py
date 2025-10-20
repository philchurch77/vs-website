from django import forms
from .models import SDQResponse

class SDQForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for i in range(1, 26):
            field = self.fields[f'q{i}']
            field.required = True
            field.empty_label = None  # This does nothing for IntegerField but is safe

            # This is key: remove the default blank choice
            if hasattr(field, 'choices'):
                field.choices = [(val, label) for val, label in field.choices if val != '']

    class Meta:
        model = SDQResponse
        fields = '__all__'
        widgets = {
            f'q{i}': forms.RadioSelect() for i in range(1, 26)
        }
        labels = {
            'q1': "Q1. Considerate of other people's feelings",
            'q2': "Q2. Restless, overactive, cannot stay still for long",
            'q3': "Q3. Often complains of headaches, stomach-aches or sickness",
            'q4': "Q4. Shares readily with other children (treats, toys, pencils etc.)",
            'q5': "Q5. Often has temper tantrums or hot tempers",
            'q6': "Q6. Rather solitary, tends to play alone",
            'q7': "Q7. Generally obedient, usually does what adults request",
            'q8': "Q8. Many worries, often seems worried",
            'q9': "Q9. Helpful if someone is hurt, upset or feeling ill",
            'q10': "Q10. onstantly fidgeting or squirming",
            'q11': "Q11. Has at least one good friend",
            'q12': "Q12. Often fights with other children or bullies them",
            'q13': "Q13. Often unhappy, down-hearted or tearful",
            'q14': "Q14. Generally liked by other children",
            'q15': "Q15. Easily distracted, concentration wanders",
            'q16': "Q16. Nervous or clingy in new situations, easily loses confidence",
            'q17': "Q17. Kind to younger children",
            'q18': "Q18. Often lies or cheats",
            'q19': "Q19. Picked on or bullied by other children",
            'q20': "Q20. Often volunteers to help others (parents, teachers, other children)",
            'q21': "Q21. Thinks things out before acting",
            'q22': "Q22. Steals from home, school or elsewhere",
            'q23': "Q23. Gets on better with adults than with other children",
            'q24': "Q24. Many fears, easily scared",
            'q25': "Q25. Sees tasks through to the end, good attention span",
        }
