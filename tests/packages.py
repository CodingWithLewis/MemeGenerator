import os


def get_size(start_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size


site_packages_path = "/home/lewismenelaws/MemeGenerator/.venv/lib/python3.10/site-packages"  # Update this path
packages = [
    os.path.join(site_packages_path, d)
    for d in os.listdir(site_packages_path)
    if os.path.isdir(os.path.join(site_packages_path, d))
]

sizes = {pkg.split("/")[-1]: get_size(pkg) for pkg in packages}
sorted_sizes = sorted(sizes.items(), key=lambda x: x[1], reverse=True)

for package, size in sorted_sizes[:10]:  # prints top 10 largest packages
    print(f"{package}: {size / (1024 * 1024)} MB")
