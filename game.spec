# -*- mode: python -*-

block_cipher = None


a = Analysis(['pogo\\game.py'],
             pathex=['C:\\PokemonGoBot\\pokemongo-api', 'C:\\PokemonGoBot\\pokemongo-api\\pogo\\pogoBot', 'C:\\PokemonGoBot\\pokemongo-api\\pogo\\pogoBot\\pogoAPI'],
             binaries=None,
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='game',
          debug=False,
          strip=False,
          upx=True,
          console=True )
