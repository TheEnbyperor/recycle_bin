import zbar
import cv2
import graphqlclient
import json

client = graphqlclient.GraphQLClient('http://localhost:8000/graphql/')

cap = cv2.VideoCapture(1)
cap.set(3, 1280)
cap.set(4, 720)
cap.set(5, 30)
scanner = zbar.Scanner()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    found = False
    results = scanner.scan(gray)
    for result in results:
        gql_result = client.execute('''
        query($barcode: String!) {
          product(barcode: $barcode) {
            id
            brand {
              id
              name
            }
            name
          }
        }
        ''', {
            "barcode": result.data.decode()
        })
        gql_result = json.loads(gql_result)['data']
        if gql_result['product'] is not None:
            print(f"{gql_result['product']['brand']['name']} {gql_result['product']['name']}")
            found = True
            break

        for pos in result.position:
            cv2.circle(frame, pos, 1, (0, 255, 0), -1)

    cv2.imshow("frame", frame)
    cv2.waitKey(1)
    if found:
        break

cap.release()
cv2.destroyAllWindows()
