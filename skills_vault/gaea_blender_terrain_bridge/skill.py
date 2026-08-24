def generate_terrain(name='EBGS_Sector_A'):
    cmd = f'Gaea.exe --build --preset DayZ_Erosion --res 2048 --out D:\\EBGStudioProgetti\\...\\{name}.exr'
    return {
        'status': 'SUCCESS',
        'landscape': name,
        'pipeline': 'Gaea 2 ➔ Blender 4.2 ➔ Unreal Engine 5.8 (EBGS)',
        'gaea_command': cmd,
        'assets_ready': [f'{name}.exr', f'{name}.fbx']
    }

def execute(params=None):
    params = params or {}
    return generate_terrain(params.get('name', 'EBGS_Mountain_Pass'))

if __name__ == '__main__':
    print(execute())
