import session
import l3_perf

def main():
    # l3_perf.upload_install_l3_perf()
    l3_perf.run_unidirection_l3_perf()
    l3_perf.run_bidirection_l3_perf()

if __name__ == "__main__":
    main()
