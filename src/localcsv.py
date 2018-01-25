import csv

def get_data(sheet, range):
	values = []   # Will contain the CSV content as an array of key:value pairs
	# Open the CSV file (in another directory in the project)
	with open('../data/ext/' + sheet + '/main.csv', 'r') as csvfile:
		reader = csv.reader(csvfile)
		headers = next(reader)[1:] # Parse the first line of the CSV and keep as headers
		for row in reader:
			# Populate the array with objects of Dictionary type (i.e. associative 
			# arrays with non-numerical keys
			dict = {key: value for key, value in zip(headers, row[1:])}
			values.append(dict)	
	if not values:
		raise RuntimeError('No data in range ' + rangeName)
	return values