import zipfile
import os
import sys
import time
import shutil
import urllib2
import subprocess

resources = [
             'Items', 
             'terrain.png', 
             'pymclevel{}pc_blockstates.json'.format(os.path.sep),
             'pymclevel{}pe_blockstates.json'.format(os.path.sep)
             ]

if '--release' in sys.argv:
    RELEASE = sys.argv[sys.argv.index('--release') + 1]
    MASTER_REPO = "MCEdit-Unified-" + RELEASE
else:
    RELEASE = None
    MASTER_REPO = "MCEdit-Unified-master"
    
def ignore_function(ignore):
    def _ignore_(path, names):
        ignored_names = []
        if ignore in names:
            ignored_names.append(ignore)
        return set(ignored_names)
    return _ignore_
        

def get_repo(branch, target_path=".", temp_path="temp"):
    if not os.path.exists(temp_path):
        os.mkdir(temp_path)
    
    if '--release' in sys.argv and branch == "master":
        url = "http://github.com/Khroki/MCEdit-Unified/archive/{}.zip".format(RELEASE)
    else:
        url = "http://github.com/Khroki/MCEdit-Unified/archive/{}.zip".format(branch)
    file_name = url.split('/')[-1]
    download_path = os.path.join(temp_path, file_name)
    
    connection = urllib2.urlopen(url)
    meta = connection.info()
    try:
        file_size = int(meta.getheaders("Content-Length")[0])
    except IndexError: # Estimate the size of the zip file
        if branch == "master":
            file_size = 24827258
        elif branch == "Docs":
            file_size = 1164882
        elif branch == "gh-pages":
            file_size = 13827762
        else:
            file_size = 10000
    fp = open(download_path, 'wb')
    
    downloaded = 0
    point = file_size / 100
    increment = file_size / 40
    block_size = 8192
    
    print "== Downloading: %s ==" % (file_name)
    while True:
        buf = connection.read(block_size)
        if not buf:
            break
        
        downloaded += len(buf)
        
        sys.stdout.write("\r[" + "=" * (downloaded / increment) +  " " * ((file_size - downloaded) / increment) + "] " +  str(downloaded / point) + "%")
        sys.stdout.flush()
        
        fp.write(buf)
        
    fp.close()
    print "\n== Downloaded: %s ==" % (file_name)
    print ""
    print "== Unzipping: %s ==" % (file_name)
    zip_handler = zipfile.ZipFile(download_path, "r")
    zip_handler.extractall(target_path)
    print "== Unzipped: %s ==" % (file_name)
    print ""

def single_main():
    get_new_sources = (raw_input("Get newest source? (Y/N): ").lower() == 'y')
    do_cleanup = (raw_input("Cleanup files? (Y/N): ").lower() == 'y')
    start_time = time.time()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    if get_new_sources: # Grab newest source
        get_repo("master")
        get_repo("gh-pages")
        get_repo("Docs")
        
    # Initialize the gh-pages repository
    print "== Initializing the gh-pages local repository =="
    os.chdir(os.path.join(base_dir, "MCEdit-Unified-gh-pages"))
    subprocess.call(["git", "init"])
    subprocess.call(["git", "remote", "add", "origin", "https://github.com/Khroki/MCEdit-Unified.git"])
    subprocess.call(["git", "fetch", "--depth=5"])
    subprocess.call(["git", "checkout", "-f", "--track", "origin/gh-pages"])
    subprocess.call(["git", "pull", "origin", "gh-pages"])
    os.chdir(base_dir)
    print "== Initialized the gh-pages local repository =="
    print ""
    
    
    for resource in resources:
        res = os.path.join(base_dir, MASTER_REPO, resource)
        dest = os.path.join(base_dir, "MCEdit-Unified-Docs", "docs", resource)
        if os.path.isdir(res):
            if os.path.exists(dest):
                shutil.rmtree(dest)
            shutil.copytree(res, dest)
        elif os.path.isfile(res):
            if not os.path.exists(os.path.dirname(dest)):
                os.makedirs(os.path.dirname(dest))
            if os.path.exists(dest):
                os.remove(dest)
            shutil.copyfile(res, dest)
    
    if os.path.exists(os.path.join(base_dir, MASTER_REPO, "docs")):
        shutil.rmtree(os.path.join(base_dir, MASTER_REPO, "docs"))        
    shutil.copytree(os.path.join(base_dir, "MCEdit-Unified-Docs", "docs"), os.path.join(base_dir, MASTER_REPO, "docs"), ignore=ignore_function([".gitignore", ".gitattributes", ".gitmodules"]))
    print "== Making Documentation =="
    os.chdir(os.path.join(base_dir, MASTER_REPO, "docs"))
    if os.path.exists(os.path.join(base_dir, "MCEdit-Unified-gh-pages", "docs")):
        shutil.rmtree(os.path.join(base_dir, "MCEdit-Unified-gh-pages", "docs"))
    
    subprocess.call([make, "html"])
    
    time.sleep(2.5)
    shutil.copytree(os.path.join(base_dir, MASTER_REPO, "docs", "_build", "html"), os.path.join(base_dir, "MCEdit-Unified-gh-pages", "docs"))
    
    os.chdir(base_dir)
    
    if do_cleanup:
        shutil.rmtree(os.path.join(".", "temp"))
    time.sleep(10)
    if do_cleanup:
        for _dir in ["master", "Docs", RELEASE]:
            if os.path.exists(os.path.join(".", "MCEdit-Unified-{}".format(_dir))):
                shutil.rmtree(os.path.join(".", "MCEdit-Unified-{}".format(_dir)))
    
    delta_time = time.time() - start_time
    print ""
    print ""
    print "Total build time took %.3f seconds" % (delta_time)
    print ""
    print "The 'MCEdit-Unified-gh-pages' directory has been left intact for review of the documentation"
    print "If you use SSH, you will need to create a new remote with the SSH URL and push to it"

if __name__ == "__main__":
    plat = sys.platform
    if plat == 'linux2':
        print "* Running on Linux. 'make' will be used. *"
        make = 'make'
    elif plat == 'win32':
        print "* Running on Windows. 'make.bat' will be used. *"
        make = 'make.bat'
    else:
        print "Your platform is not supported, but may be."
        print "'sys.platform' said:", plat
        print "Edit this script and configure the 'make' file for your platform, if you know how to build Sphinx docs on it."
        sys.exit(1)
    single_main()
