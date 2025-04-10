import toml 

with open('config.toml') as f:
    data = toml.load(f)

print(data)