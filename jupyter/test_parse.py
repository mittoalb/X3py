import argparse

def main():

	parser = argparse.ArgumentParser(description='3D Xanes Python Processing Tool')
	parser.add_argument('--filename', type=str, help='First file name to be processed',default='tiff')
	parser.add_argument('--method', type=str, help='Registration method',default='TranslationTransform')
	parser.add_argument('--config', type=str, help='Provide Config file',default='config.json')
	parser.add_argument('--log', type=str, help='Custom log file',default='x3py.log')
	
	
	args = parser.parse_args()
	print(args.filename)
	
if __name__ == "__main__":
	main()
