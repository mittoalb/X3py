from utils import distribute_jobs



def main():
    def runreg(i):
        print('1')

    distribute_jobs(runreg, range(10))

if __name__ == "__main__":
	main()
