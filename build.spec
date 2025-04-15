a = Analysis(
    ['main.py'],
    datas=[
        ('fonts/*', 'fonts'),
        ('styles/*', 'styles')
    ],
    ...
)