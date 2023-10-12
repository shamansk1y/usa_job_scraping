from django.db import models


class Vacancy(models.Model):
    url = models.TextField(max_length=500)
    title = models.CharField(max_length=250, verbose_name='Name vacancy')
    company = models.CharField(max_length=250, verbose_name='Company')
    description = models.TextField(verbose_name='Vacancy description')
    search_source = models.CharField(max_length=250, verbose_name='Search source')
    timestamp = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = 'Job vacancy'
        verbose_name_plural = 'Vacancies'
        ordering = ['-timestamp']

    def __str__(self):
        return self.title
