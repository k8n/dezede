# coding: utf-8
from __future__ import print_function
from django.core.files import File
from unipath import Path
from libretto.models import Fichier


EXTENSIONS = (u'mp4', u'ogg')
FILENAMES = (#u'JEAUA000001_01', u'JEAUA000001_02', u'JEAUA000001_03',
#              u'JEAUA000001_04', u'JEAUA000001_05', u'JEAUA000001_06',
#              u'JEAUA000001_07', u'JEAUA000001_08', u'JEAUA000002_01',
#              u'JEAUA000002_02', u'JEAUA000002_03', u'JEAUA000002_04',
#              u'JEAUA000002_05', u'JEAUA000002_06', u'JEAUA000002_07',
#              u'JEAUA000003_01', u'JEAUA000003_02', u'JEAUA000003_03',
#              u'JEAUA000003_04', u'JEAUA000003_05', u'JEAUA000003_06',
#              u'JEAUA000004_01', u'JEAUA000004_02', u'JEAUA000004_03',
#              u'JEAUA000004_04', u'JEAUA000004_05', u'JEAUA000004_06',
#              u'JEAUA000004_07', u'JEAUA000004_08', u'DIAUA000001_01',
#              u'DIAUA000001_02', u'DIAUA000001_03', u'DIAUA000002_01',
#              u'DIAUA000003_01', u'DIAUA000004_01', u'BAAUA000001_01',
#              u'BAAUA000001_02', u'BAAUA000001_03', u'BAAUA000001_04',
#              u'BAAUA000001_05', u'BAAUA000001_06', u'BAAUA000001_07',
#              u'BAAUA000001_08', u'BAAUA000001_09', u'BAAUA000002_01',
#              u'BAAUA000002_02', u'BAAUA000003_01', u'BAAUA000003_02',
#              u'BAAUA000003_03', u'BAAUA000003_04', u'BAAUA000004_01',
#              u'BAAUA000004_02', u'BAAUA000004_03', u'BAAUA000004_04',
#              u'BAAUA000005_01', u'BAAUA000005_02', u'BAAUA000005_03',
#              u'BAAUA000005_04', u'BAAUA000005_05', u'BAAUA000005_06',
#              u'BAAUA000005_07', u'BAAUA000006_01', u'BAAUA000006_02',
#              u'BAAUA000006_03', u'BAAUA000006_04', u'BAAUA000006_05',
#              u'BAAUA000006_06', u'BAAUA000006_07', u'BAAUA000007_01',
#              u'BAAUA000007_02', u'BAAUA000007_03', u'BAAUA000007_04',
#              u'BAAUA000008_01', u'BAAUA000008_02', u'BAAUA000008_03',
#              u'BAAUA000008_04', u'BAAUA000008_05', u'BAAUA000008_06',
#              u'BAAUA000008_07', u'BAAUA000008_08', u'BAAUA000008_09',
#              u'BAAUA000009_01', u'BAAUA000009_02', u'BAAUA000009_03',
#              u'BAAUA000009_04', u'BAAUA000010_01', u'BAAUA000010_02',
#              u'BAAUA000010_03', u'BAAUA000011_01', u'BAAUA000011_02',
#              u'BAAUA000011_03', u'BAAUA000011_04', u'BAAUA000012_01',
#              u'BAAUA000012_02', u'BAAUA000013_01', u'BAAUA000013_02',
#              u'BAAUA000013_03', u'BAAUA000014_01', u'BAAUA000014_02',
#              u'BAAUA000014_03', u'BAAUA000015_01', u'BAAUA000015_02',
#              u'BAAUA000015_03', u'BAAUA000015_04', u'BAAUA000015_05',
#              u'BAAUA000015_06', u'BAAUA000015_07', u'BAAUA000015_08',
#              u'BAAUA000016_01', u'BAAUA000016_02', u'BAAUA000016_03',
#              u'BAAUA000016_04', u'BAAUA000016_05', u'BAAUA000017_01',
#              u'BAAUA000017_02', u'BAAUA000017_03', u'BAAUA000018_01',
#              u'BAAUA000018_02', u'BAAUA000019_01', u'BAAUA000019_02',
#              u'BAAUA000019_03', u'BAAUA000019_04', u'BAAUA000020_01',
#              u'BAAUA000020_02', u'BAAUA000021_01', u'BAAUA000021_02',
#              u'BAAUA000022_01', u'BAAUA000022_02', u'BAAUA000022_03',
#              u'BAAUA000023_01', u'BAAUA000023_02', u'BAAUA000023_03',
#              u'BAAUA000023_04', u'AUAUA000000_01', u'AUAUA000000_02',
#              u'AUAUA000000_03', u'AUAUA000000_04', u'AUAUA000001_01',
#              u'AUAUA000001_02', u'AUAUA000001_03', u'AUAUA000002_01',
#              u'AUAUA000002_02', u'AUAUA000002_03', u'AUAUA000002_04',
#              u'AUAUA000003_01', u'AUAUA000004_01', u'AUAUA000004_02',
#              u'AUAUA000004_03', u'AUAUA000004_04', u'AUAUA000004_05',
#              u'AUAUA000004_06', u'AUAUA000005_01', u'AUAUA000005_02',
#              u'AUAUA000005_03', u'AUAUA000006_01', u'AUAUA000006_02',
#              u'AUAUA000007_01', u'AUAUA000007_02', u'AUAUA000008_01',
#              u'AUAUA000008_02', u'AUAUA000009_01', u'AUAUA000009_02',
#              u'AUAUA000009_03', u'AUAUA000009_04', u'AUAUA000009_05',
#              u'AUAUA000010_01', u'AUAUA000010_02', u'AUAUA000010_03',
#              u'AUAUA000010_04', u'AUAUA000010_05', u'AUAUA000010_06',
#              u'AUAUA000011_01', u'AUAUA000011_02', u'AUAUA000011_03',
#              u'AUAUA000011_04', u'AUAUA000011_05', u'AUAUA000011_06',
#              u'AUAUA000012_01', u'AUAUA000012_02', u'AUAUA000012_03',
#              u'AUAUA000012_04', u'AUAUA000012_05', u'AUAUA000012_06',
#              u'AUAUA000012_07', u'AUAUA000012_08', u'AUAUA000012_09',
#              u'AUAUA000013_01', u'AUAUA000013_02', u'AUAUA000013_03',
#              u'AUAUA000014_01', u'AUAUA000014_02', u'AUAUA000014_03',
#              u'AUAUA000014_04', u'AUAUA000015_01', u'AUAUA000015_02',
#              u'AUAUA000015_03', u'AUAUA000015_04', u'AUAUA000016_01',
#              u'AUAUA000016_02', u'AUAUA000016_03', u'AUAUA000016_04',
#              u'AUAUA000017_01', u'AUAUA000017_02', u'AUAUA000018_01',
#              u'AUAUA000018_02', u'AUAUA000018_03', u'AUAUA000018_04',
#              u'AUAUA000019_01', u'AUAUA000019_02', u'AUAUA000019_03',
#              u'AUAUA000019_04', u'AUAUA000019_05', u'AUAUA000020_01',
#              u'AUAUA000020_02', u'AUAUA000020_03', u'AUAUA000020_04',
#              u'AUAUA000021_01', u'AUAUA000021_02', u'AUAUA000021_03',
#              u'AUAUA000021_04', u'AUAUA000022_01', u'AUAUA000022_02',
#              u'AUAUA000022_03', u'AUAUA000022_04', u'AUAUA000023_01',
#              u'AUAUA000023_02', u'AUAUA000023_03', u'AUAUA000023_04',
#              u'AUAUA000023_05', u'AUAUA000024_01', u'AUAUA000024_02',
#              u'AUAUA000024_03', u'AUAUA000024_04', u'AUAUA000024_05',
#              u'AUAUA000024_06', u'AUAUA000025_01', u'AUAUA000025_02',
#              u'AUAUA000025_03', u'AUAUA000025_04', u'AUAUA000026_01',
#              u'AUAUA000026_02', u'AUAUA000026_03', u'AUAUA000026_04',
#              u'AUAUA000027_01', u'AUAUA000027_02', u'AUAUA000027_03',
#              u'AUAUA000027_04', u'AUAUA000027_05', u'AUAUA000027_06',
#              u'AUAUA000028_01', u'AUAUA000028_02', u'AUAUA000028_03',
#              u'AUAUA000028_04', u'AUAUA000029_01', u'AUAUA000029_02',
#              u'AUAUA000029_03', u'AUAUA000030_01', u'AUAUA000030_02',
#              u'AUAUA000030_03', u'AUAUA000031_01', u'AUAUA000031_02',
#              u'AUAUA000032_01', u'AUAUA000032_02', u'AUAUA000032_03',
#              u'AUAUA000032_04', u'AUAUA000032_05', u'AUAUA000033_01',
#              u'AUAUA000033_02', u'AUAUA000033_03', u'AUAUA000034_01',
#              u'AUAUA000034_02', u'AUAUA000034_03', u'AUAUA000034_04',
#              u'AUAUA000035_01', u'AUAUA000035_02', u'AUAUA000035_03',
#              u'AUAUA000035_04', u'AUAUA000035_05', u'AUAUA000035_06',
#              u'AUAUA000035_07', u'AUAUA000035_08', u'AUAUA000035_09',
#              u'AUAUA000035_10', u'AUAUA000035_11', u'AUAUA000035_12',
#              u'AUAUA000035_13', u'AUAUA000035_14', u'AUAUA000035_15',
#              u'AUAUA000035_16', u'AUAUA000035_17', u'AUAUA000035_18',
#              u'AUAUA000035_19', u'AUAUA000035_20', u'AUAUA000035_21',
#              u'AUAUA000036_01', u'AUAUA000036_02', u'AUAUA000037_01',
#              u'AUAUA000038_01', u'AUAUA000038_02', u'AUAUA000038_03',
#              u'AUAUA000039_01', u'AUAUA000039_02', u'AUAUA000040_01',
#              u'AUAUA000040_02', u'AUAUA000041_01', u'AUAUA000041_02',
#              u'AUAUA000042_01', u'AUAUA000042_02', u'AUAUA000042_03',
#              u'AUAUA000042_04', u'AUAUA000043_01', u'AUAUA000043_02',
#              u'AUAUA000044_01', u'AUAUA000044_02', u'AUAUA000044_03',
#              u'AUAUA000045_01', u'AUAUA000045_02', u'AUAUA000045_03',
#              u'AUAUA000045_04', u'AUAUA000045_05', u'AUAUA000046_01',
#              u'AUAUA000046_02', u'AUAUA000046_03', u'AUAUA000046_04',
#              u'AUAUA000046_05', u'AUAUA000046_06', u'AUAUA000046_07',
#              u'AUAUA000046_08', u'AUAUA000046_09', u'AUAUA000046_10',
#              u'AUAUA000046_11', u'AUAUA000046_12', u'AUAUA000046_13',
#              u'AUAUA000046_14', u'AUAUA000046_15', u'AUAUA000046_16',
#              u'AUAUA000047_01', u'AUAUA000047_02', u'AUAUA000047_03',
#              u'AUAUA000047_04', u'AUAUA000047_05', u'AUAUA000047_06',
#              u'AUAUA000047_07', u'AUAUA000047_08', u'AUAUA000047_09',
#              u'AUAUA000047_10', u'AUAUA000047_11', u'AUAUA000048_01',
#              u'AUAUA000048_02', u'AUAUA000048_03', u'AUAUA000048_04',
#              u'AUAUA000049_01', u'AUAUA000049_02', u'AUAUA000049_03',
#              u'AUAUA000049_04', u'AUAUA000049_05', u'AUAUA000049_06',
#              u'AUAUA000049_07', u'AUAUA000049_08', u'AUAUA000049_09',
#              u'AUAUA000049_10', u'AUAUA000050_01', u'AUAUA000050_02',
#              u'AUAUA000050_03', u'AUAUA000050_04', u'AUAUA000050_05',
#              u'AUAUA000051_01', u'AUAUA000051_02', u'AUAUA000051_03',
#              u'AUAUA000051_04', u'AUAUA000051_05', u'AUAUA000051_06',
#              u'AUAUA000051_07', u'AUAUA000052_01', u'AUAUA000052_02',
#              u'AUAUA000052_03', u'AUAUA000052_04', u'AUAUA000052_05',
#              u'AUAUA000053_01', u'AUAUA000053_02', u'AUAUA000053_03',
#              u'AUAUA000053_04', u'AUAUA000053_05', u'AUAUA000053_06',
#              u'AUAUA000053_07', u'AUAUA000053_08', u'AUAUA000053_09',
#              u'AUAUA000053_10', u'AUAUA000053_11', u'AUAUA000053_12',
#              u'AUAUA000053_13', u'AUAUA000053_14', u'AUAUA000053_15',
#              u'AUAUA000053_16', u'AUAUA000053_17', u'AUAUA000053_18',
#              u'AUAUA000053_19', u'AUAUA000053_20', u'AUAUA000053_21',
#              u'AUAUA000053_22', u'AUAUA000053_23', u'AUAUA000053_24',
#              u'AUAUA000054_01', u'AUAUA000054_02', u'AUAUA000054_03',
#              u'AUAUA000055_01', u'AUAUA000055_02', u'AUAUA000056_01',
             u'AUAUA000056_02', u'AUAUA000057_01', u'AUAUA000057_02',
             u'AUAUA000057_03', u'AUAUA000058_01', u'AUAUA000058_02',
             u'AUAUA000058_03', u'AUAUA000059_01', u'AUAUA000059_02',
             u'AUAUA000059_03', u'AUAUA000060_01', u'AUAUA000060_02',
             u'AUAUA000060_03', u'AUAUA000060_04', u'AUAUA000061_01',
             u'AUAUA000062_01', u'AUAUA000062_02', u'AUAUA000062_03',
             u'AUAUA000063_01', u'AUAUA000063_02', u'AUAUA000064_01',
             u'AUAUA000064_02', u'AUAUA000064_03', u'AUAUA000065_01',
             u'AUAUA000065_02', u'AUAUA000065_03', u'AUAUA000065_04',
             u'AUAUA000065_05', u'AUAUA000066_01', u'AUAUA000066_02',
             u'AUAUA000066_03', u'AUAUA000067_01', u'AUAUA000067_02',
             u'AUAUA000067_03', u'AUAUA000067_04', u'AUAUA000068_12',
             u'AUAUA000069_01', u'AUAUA000069_02', u'AUAUA000069_03',
             u'AUAUA000069_04', u'AUAUA000069_05', u'AUAUA000069_06',
             u'AUAUA000071_01', u'AUAUA000071_02', u'AUAUA000071_03',
             u'AUAUA000071_04', u'AUAUA000072_01', u'AUAUA000072_02',
             u'AUAUA000072_03', u'AUAUA000072_04', u'AUAUA000072_05',
             u'AUAUA000073_01', u'AUAUA000073_02', u'AUAUA000073_03',
             u'AUAUA000073_04', u'AUAUA000074_01', u'AUAUA000074_02',
             u'AUAUA000074_03', u'AUAUA000074_04')


def run(records_path):
    records_path = Path(records_path)
    total = float(len(FILENAMES) * len(EXTENSIONS))
    i = 0
    for ext in EXTENSIONS:
        for filename in FILENAMES:
            extract = Fichier.objects.get(
                fichier=u'files/' + filename + Fichier.EXTRACT_INFIX + u'.' + ext)
            s = filename.split('_')[0]
            with open(records_path.child(s[:2], s, filename + u'.' + ext)) as f:
                Fichier.objects.create(source=extract.source, extract=extract,
                                       position=extract.position, fichier=File(f))
            i += 1
            print('%.2f %%' % (100 * i / total), end='\r')