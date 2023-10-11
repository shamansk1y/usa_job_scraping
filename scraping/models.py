from django.db import models


class Vacancy(models.Model):
    url = models.CharField(max_length=250)
    url_2 = models.CharField(max_length=250, blank=True, null=True)
    title = models.CharField(max_length=250, verbose_name='Name vacancy')
    company = models.CharField(max_length=250, verbose_name='Company')
    description = models.TextField(verbose_name='Vacancy description')
    search_source = models.CharField(max_length=250, verbose_name='Search source')
    timestamp = models.DateField(auto_now_add=True)

    def full_url(self):
        if self.url_2:
            return self.url + self.url_2
        else:
            return self.url


    class Meta:
        verbose_name = 'Job vacancy'
        verbose_name_plural = 'Vacancies'
        ordering = ['-timestamp']

    def __str__(self):
        return self.title
