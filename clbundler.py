from config import global_config
        
def main():
    print global_config().workspace_dir()
    print global_config().root_dir()
    global_config().write()
        
if __name__ == "__main__":
    main()
