from cx_Freeze import setup, Executable

includefiles = [('pogo/templates/', 'templates'), ('pogo/static/', 'static'), ('pogo/pogoBot', 'pogoBot'),
                ('pogo/pogoBot/pogoAPI', 'pogoBot/pogoAPI'), 'pogo/POGOProtos']
packages = ['jinja2','jinja2.ext','os','geocoder', 'gpxpy', 'geopy', 's2sphere', 'gpsoauth']
base = None

main_executable = Executable("pogo/game.py", base=base, copyDependentFiles=True)

setup(name="Example",
      version="0.1",
      description="Example Web Server",
      options={
      'build_exe': {
          'packages': packages,
          'include_files': includefiles,
          'include_msvcr': True}},
      executables=[main_executable], requires=['flask'])