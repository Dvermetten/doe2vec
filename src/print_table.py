import json
  
# Opening JSON file
f = open('new_results_class.json')
  
# returns JSON object as 
# a dictionary
data = json.load(f)
print(data)
f.close()
print( "\\toprule")
print( "Task \t&\t", end="")

for alg in data:
    print( alg + "\t&\t", end="")
print("\\\\")
print("\\midrule")

for prob in data["dense"]:
    print(prob + "\t&\t", end="")
    for alg in data:
        if (prob in data[alg]):
            print(format(data[alg][prob],".3f"), end="")
        else:
            print("-", end="")
        print("\t&\t", end="")
    print("\\\\")