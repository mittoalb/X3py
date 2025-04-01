import x3py
from x3py.config import ProInit
from x3py.itkreg import ITKregistration


#Initialize config and register
ref_name = 'test_config.json'
pI = ProInit(ref_name)

extra_args = [ref_name,'TranslationTransform']
itkr = ITKregistration(extra_args, pI.ReturnParameters())


dic = pI.ReturnParameters()
prefix = dic['DataPrefix']
epoints = 20


#ref, paths = getFolderList(prefix,epoints)
#print(ref,paths)

#
itkr.CTREG()
