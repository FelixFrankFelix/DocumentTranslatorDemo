
decoded_key = "en|fr|name.docx"

split_name = decoded_key.split(".")
extension = split_name[-1]
name_desc = split_name[0].split('|')
print(split_name)
print(extension,name_desc)
file_name = name_desc[2]
source_language = name_desc[0]
target_language = name_desc[1]
print(file_name,source_language,target_language)
file_name = file_name+target_language+'.'+extension
print(file_name)