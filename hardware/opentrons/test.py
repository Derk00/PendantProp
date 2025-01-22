

test_dict = {"x": 5, "y":3}
test_dict_update = {"x": 2, "y":3}

for key in test_dict_update:
    test_dict[key] += test_dict_update[key]

print(test_dict)