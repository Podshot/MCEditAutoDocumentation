import zipfile
import os
import sys
import time
import shutil
import urllib2
import subprocess

resources = ['Items', 'terrain.png']
    
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
    print "== Unzipping: %s ==" % (file_name)
    zip_handler = zipfile.ZipFile(download_path, "r")
    zip_handler.extractall(target_path)
    print "== Unzipped: %s ==" % (file_name)

def single_main():
    get_new_soruces = (raw_input("Get newest source? (Y/N): ").lower() == 'y')
    do_cleanup = (raw_input("Cleanup files? (Y/N): ").lower() == 'y')
    start_time = time.time()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    if get_new_soruces:
        get_repo("master")
        get_repo("gh-pages")
        get_repo("Docs")
    
    for resource in resources:
        res = os.path.join(base_dir, "MCEdit-Unified-master", resource)
        dest = os.path.join(base_dir, "MCEdit-Unified-Docs", "docs", resource)
        if os.path.isdir(res):
            if os.path.exists(dest):
                shutil.rmtree(dest)
            shutil.copytree(res, dest)
        elif os.path.isfile(res):
            if os.path.exists(dest):
                os.remove(dest)
            shutil.copyfile(res, dest)
    
    if os.path.exists(os.path.join(base_dir, "MCEdit-Unified-master", "docs")):
        shutil.rmtree(os.path.join(base_dir, "MCEdit-Unified-master", "docs"))        
    shutil.copytree(os.path.join(base_dir, "MCEdit-Unified-Docs", "docs"), os.path.join(base_dir, "MCEdit-Unified-master", "docs"), ignore=ignore_function([".gitignore", ".gitattributes", ".gitmodules"]))
    print "== Making Documentation =="
    os.chdir(os.path.join(base_dir, "MCEdit-Unified-master", "docs"))
    
    subprocess.call([make, "html"])
    
    time.sleep(2.5)
    shutil.rmtree(os.path.join(base_dir, "MCEdit-Unified-gh-pages", "docs"))
    shutil.copytree(os.path.join(base_dir, "MCEdit-Unified-master", "docs", "_build", "html"), os.path.join(base_dir, "MCEdit-Unified-gh-pages", "docs"))
    
    os.chdir(base_dir)
    
    shutil.rmtree(os.path.join(".", "temp"))
    time.sleep(10)
    if do_cleanup:
        for _dir in ["master", "Docs"]:
            shutil.rmtree(os.path.join(".", "MCEdit-Unified-{}".format(_dir)))
        print "The 'MCEdit-Unified-gh-pages' directory has been left intact for review of the documentation"
    
    delta_time = time.time() - start_time
    print "Total build time took %.3f seconds" % (delta_time)

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
