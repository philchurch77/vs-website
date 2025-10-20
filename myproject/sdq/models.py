from django.db import models

class SDQResponse(models.Model):
    Response_Choices_1 = [(0, 'Not True'), (1, 'Somewhat True'), (2, 'Certainly True')]
    Response_Choices_2 = [(2, 'Not True'), (1, 'Somewhat True'), (0, 'Certainly True')]

    q1 = models.IntegerField(choices=Response_Choices_1, null=False, blank=False)
    q2 = models.IntegerField(choices=Response_Choices_1, null=False, blank=False)
    q3 = models.IntegerField(choices=Response_Choices_1, null=False, blank=False)
    q4 = models.IntegerField(choices=Response_Choices_1, null=False, blank=False)
    q5 = models.IntegerField(choices=Response_Choices_1, null=False, blank=False)
    q6 = models.IntegerField(choices=Response_Choices_1, null=False, blank=False)
    q7 = models.IntegerField(choices=Response_Choices_2, null=False, blank=False)
    q8 = models.IntegerField(choices=Response_Choices_1, null=False, blank=False)
    q9 = models.IntegerField(choices=Response_Choices_1, null=False, blank=False)
    q10 = models.IntegerField(choices=Response_Choices_1, null=False, blank=False)
    q11 = models.IntegerField(choices=Response_Choices_2, null=False, blank=False)
    q12 = models.IntegerField(choices=Response_Choices_1, null=False, blank=False)
    q13 = models.IntegerField(choices=Response_Choices_1, null=False, blank=False)
    q14 = models.IntegerField(choices=Response_Choices_2, null=False, blank=False)
    q15 = models.IntegerField(choices=Response_Choices_1, null=False, blank=False)
    q16 = models.IntegerField(choices=Response_Choices_1, null=False, blank=False)
    q17 = models.IntegerField(choices=Response_Choices_1, null=False, blank=False)
    q18 = models.IntegerField(choices=Response_Choices_1, null=False, blank=False)
    q19 = models.IntegerField(choices=Response_Choices_1, null=False, blank=False)
    q20 = models.IntegerField(choices=Response_Choices_1, null=False, blank=False)
    q21 = models.IntegerField(choices=Response_Choices_2, null=False, blank=False)
    q22 = models.IntegerField(choices=Response_Choices_1, null=False, blank=False)
    q23 = models.IntegerField(choices=Response_Choices_1, null=False, blank=False)
    q24 = models.IntegerField(choices=Response_Choices_1, null=False, blank=False)
    q25 = models.IntegerField(choices=Response_Choices_2, null=False, blank=False)

    def total_score(self):
            excluded = {1, 4, 9, 17, 20}
            return sum(
                getattr(self, f"q{i}") 
                for i in range(1, 26) 
                if i not in excluded
            )

    def emotional_problems_score(self):
        return self.q3 + self.q8 + self.q13 + self.q16 + self.q24
    
    def conduct_problems_scale(self):
        return self.q5 + self.q7 + self.q12 + self.q18 + self.q22
    
    def hyperactivity_scale(self):
        return self.q2 + self.q10 + self.q15 + self.q21 + self.q25
    
    def peer_problems_scale(self):
        return self.q6 + self.q11 + self.q14 + self.q19 + self.q23
    
    def prosocial_scale(self):
        return self.q1 + self.q4 + self.q9 + self.q17 + self.q20