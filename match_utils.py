def isMatch(response_objects, challenge_object):

	# iterate the response array, compare each with the challenge's object
	# if match, return true; else return false
	for obj in response_objects:
		if obj == challenge_object:
			return True

	return False